import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

import firebase_admin
from firebase_admin import credentials, firestore
from app.config import settings
from scripts.seed_data import generate_seed_data

class FirebaseService:
    def __init__(self):
        self.db = None
        self.use_fallback = False
        self._fallback_data: Dict[str, Dict[str, Any]] = {}
        self._fallback_conversations: Dict[str, Dict[str, Any]] = {}
        self._init_firebase()

    def _init_firebase(self):
        """
        환경 변수로부터 Firebase Admin SDK를 초기화합니다.
        키가 없거나 유효하지 않은 경우 로컬 개발용 Fallback 모드로 안전하게 구동합니다.
        """
        try:
            # 1) JSON 문자열 환경변수 확인
            if settings.FIREBASE_SERVICE_ACCOUNT_JSON:
                try:
                    cred_dict = json.loads(settings.FIREBASE_SERVICE_ACCOUNT_JSON)
                    cred = credentials.Certificate(cred_dict)
                    if not firebase_admin._apps:
                        firebase_admin.initialize_app(cred)
                    self.db = firestore.client()
                    print("[FirebaseService] Successfully connected to Firestore using FIREBASE_SERVICE_ACCOUNT_JSON.")
                    self._check_and_seed_data()
                    return
                except Exception as e:
                    print(f"[FirebaseService] Error parsing FIREBASE_SERVICE_ACCOUNT_JSON: {e}")

            # 2) 파일 경로 환경변수 확인
            key_path = settings.FIREBASE_SERVICE_ACCOUNT_KEY_PATH
            if key_path and os.path.exists(key_path):
                try:
                    cred = credentials.Certificate(key_path)
                    if not firebase_admin._apps:
                        firebase_admin.initialize_app(cred)
                    self.db = firestore.client()
                    print(f"[FirebaseService] Successfully connected to Firestore using key file: {key_path}")
                    self._check_and_seed_data()
                    return
                except Exception as e:
                    print(f"[FirebaseService] Error loading key file {key_path}: {e}")

            # 3) 키가 없거나 초기화 실패 시 로컬 Fallback 모드 가동
            print("[FirebaseService] Notice: Firebase credentials not found or invalid. Running in Local Fallback mode.")
            self.use_fallback = True
            self._seed_fallback_data()

        except Exception as ex:
            print(f"[FirebaseService] Unexpected error during Firebase init: {ex}. Falling back to local store.")
            self.use_fallback = True
            self._seed_fallback_data()

    def _check_and_seed_data(self):
        """실제 Firestore에 데이터가 없으면 최소 요건 충족을 위해 120개 시드 데이터를 채웁니다."""
        try:
            docs = list(self.db.collection("data").limit(1).stream())
            if not docs:
                print("[FirebaseService] Firestore collection 'data' is empty. Seeding initial 120 records...")
                seeds = generate_seed_data(count=120)
                batch = self.db.batch()
                for item in seeds:
                    doc_ref = self.db.collection("data").document(item["id"])
                    batch.set(doc_ref, item)
                batch.commit()
                print(f"[FirebaseService] Successfully seeded {len(seeds)} records to Firestore.")
        except Exception as e:
            print(f"[FirebaseService] Failed to seed initial data to Firestore: {e}")

    def _seed_fallback_data(self):
        """로컬 Fallback 모드 시 120개 시드 데이터 적재"""
        seeds = generate_seed_data(count=120)
        for item in seeds:
            self._fallback_data[item["id"]] = item
        print(f"[FirebaseService] Initialized fallback store with {len(seeds)} seed records.")

    # ==========================
    # DATA CRUD (Collection: data)
    # ==========================

    def create_data(self, item: Dict[str, Any]) -> Dict[str, Any]:
        doc_id = item.get("id") or f"data_{uuid.uuid4().hex[:10]}"
        now = datetime.now().isoformat()
        record = {
            "id": doc_id,
            "date": item["date"],
            "value": int(item["value"]),
            "memo": item.get("memo", ""),
            "created_at": now,
            "updated_at": now
        }

        if not self.use_fallback and self.db:
            try:
                self.db.collection("data").document(doc_id).set(record)
                return record
            except Exception as e:
                print(f"[FirebaseService] Firestore create_data error: {e}. Storing locally.")

        self._fallback_data[doc_id] = record
        return record

    def get_all_data(self) -> List[Dict[str, Any]]:
        if not self.use_fallback and self.db:
            try:
                docs = self.db.collection("data").order_by("date").stream()
                results = [doc.to_dict() for doc in docs]
                return results
            except Exception as e:
                print(f"[FirebaseService] Firestore get_all_data error: {e}. Reading fallback.")

        # Fallback 정렬
        records = list(self._fallback_data.values())
        return sorted(records, key=lambda x: str(x.get("date", "")))

    def get_data_by_id(self, item_id: str) -> Optional[Dict[str, Any]]:
        if not self.use_fallback and self.db:
            try:
                doc = self.db.collection("data").document(item_id).get()
                if doc.exists:
                    return doc.to_dict()
                return None
            except Exception as e:
                print(f"[FirebaseService] Firestore get_data_by_id error: {e}")

        return self._fallback_data.get(item_id)

    def update_data(self, item_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        now = datetime.now().isoformat()
        cleaned_updates = {k: v for k, v in updates.items() if v is not None}
        cleaned_updates["updated_at"] = now

        if not self.use_fallback and self.db:
            try:
                doc_ref = self.db.collection("data").document(item_id)
                doc = doc_ref.get()
                if not doc.exists:
                    return None
                doc_ref.update(cleaned_updates)
                updated_doc = doc_ref.get().to_dict()
                return updated_doc
            except Exception as e:
                print(f"[FirebaseService] Firestore update_data error: {e}")

        if item_id not in self._fallback_data:
            return None
        self._fallback_data[item_id].update(cleaned_updates)
        return self._fallback_data[item_id]

    def delete_data(self, item_id: str) -> bool:
        if not self.use_fallback and self.db:
            try:
                doc_ref = self.db.collection("data").document(item_id)
                if not doc_ref.get().exists:
                    return False
                doc_ref.delete()
                return True
            except Exception as e:
                print(f"[FirebaseService] Firestore delete_data error: {e}")

        if item_id in self._fallback_data:
            del self._fallback_data[item_id]
            return True
        return False

    # ==========================
    # CONVERSATIONS CRUD (Collection: conversations)
    # ==========================

    def create_conversation(self, conv: Dict[str, Any]) -> Dict[str, Any]:
        conv_id = conv.get("id") or f"conv_{uuid.uuid4().hex[:10]}"
        now = datetime.now().isoformat()
        messages = conv.get("messages", [])
        title = conv.get("title") or (messages[0]["content"][:30] if messages else "새로운 대화")

        record = {
            "id": conv_id,
            "title": title,
            "messages": messages,
            "created_at": now,
            "updated_at": now
        }

        if not self.use_fallback and self.db:
            try:
                self.db.collection("conversations").document(conv_id).set(record)
                return record
            except Exception as e:
                print(f"[FirebaseService] Firestore create_conversation error: {e}")

        self._fallback_conversations[conv_id] = record
        return record

    def get_conversations(self) -> List[Dict[str, Any]]:
        if not self.use_fallback and self.db:
            try:
                docs = self.db.collection("conversations").order_by("updated_at", direction=firestore.Query.DESCENDING).stream()
                return [doc.to_dict() for doc in docs]
            except Exception as e:
                print(f"[FirebaseService] Firestore get_conversations error: {e}")

        items = list(self._fallback_conversations.values())
        return sorted(items, key=lambda x: str(x.get("updated_at", "")), reverse=True)

    def get_conversation_by_id(self, conv_id: str) -> Optional[Dict[str, Any]]:
        if not self.use_fallback and self.db:
            try:
                doc = self.db.collection("conversations").document(conv_id).get()
                if doc.exists:
                    return doc.to_dict()
                return None
            except Exception as e:
                print(f"[FirebaseService] Firestore get_conversation_by_id error: {e}")

        return self._fallback_conversations.get(conv_id)

    def append_messages(self, conv_id: str, new_messages: List[Dict[str, Any]], title_candidate: Optional[str] = None) -> Optional[Dict[str, Any]]:
        conv = self.get_conversation_by_id(conv_id)
        now = datetime.now().isoformat()
        if not conv:
            # 새로 생성
            title = title_candidate or (new_messages[0]["content"][:30] if new_messages else "대화 세션")
            return self.create_conversation({
                "id": conv_id,
                "title": title,
                "messages": new_messages
            })

        current_messages = conv.get("messages", [])
        current_messages.extend(new_messages)
        
        updates = {
            "messages": current_messages,
            "updated_at": now
        }
        if title_candidate and conv.get("title") in ["새로운 대화", "대화 세션", ""]:
            updates["title"] = title_candidate[:30]

        if not self.use_fallback and self.db:
            try:
                doc_ref = self.db.collection("conversations").document(conv_id)
                doc_ref.update(updates)
                conv.update(updates)
                return conv
            except Exception as e:
                print(f"[FirebaseService] Firestore append_messages error: {e}")

        if conv_id in self._fallback_conversations:
            self._fallback_conversations[conv_id].update(updates)
            return self._fallback_conversations[conv_id]
        return None

    def delete_conversation(self, conv_id: str) -> bool:
        if not self.use_fallback and self.db:
            try:
                doc_ref = self.db.collection("conversations").document(conv_id)
                if not doc_ref.get().exists:
                    return False
                doc_ref.delete()
                return True
            except Exception as e:
                print(f"[FirebaseService] Firestore delete_conversation error: {e}")

        if conv_id in self._fallback_conversations:
            del self._fallback_conversations[conv_id]
            return True
        return False

firebase_service = FirebaseService()
