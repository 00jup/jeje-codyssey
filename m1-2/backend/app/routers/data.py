from fastapi import APIRouter, HTTPException, status
from typing import List
from app.models.data import DataCreate, DataUpdate, DataResponse, DataSummary
from app.services.firebase_service import firebase_service
from app.services.analysis_service import analysis_service

router = APIRouter(prefix="/api/data", tags=["Data"])

@router.get("/summary", response_model=DataSummary, summary="데이터 요약 통계 조회 (프롬프트 주입용)")
def get_data_summary():
    """
    저장된 모든 시계열 데이터를 분석하여 요약 정보(기간, 개수, 통계, 트렌드)를 반환합니다.
    """
    records = firebase_service.get_all_data()
    summary = analysis_service.compute_summary(records)
    return summary

@router.post("", response_model=DataResponse, status_code=status.HTTP_201_CREATED, summary="새 데이터 추가")
def create_data_item(payload: DataCreate):
    """
    새로운 일별 매출 시계열 데이터를 추가합니다.
    """
    record = firebase_service.create_data(payload.model_dump())
    return record

@router.get("", response_model=List[DataResponse], summary="데이터 목록 조회")
def get_data_list():
    """
    날짜순으로 정렬된 전체 매출 데이터 목록을 조회합니다.
    """
    return firebase_service.get_all_data()

@router.get("/{item_id}", response_model=DataResponse, summary="특정 데이터 상세 조회")
def get_data_item(item_id: str):
    record = firebase_service.get_data_by_id(item_id)
    if not record:
        raise HTTPException(status_code=404, detail="해당 ID의 데이터를 찾을 수 없습니다.")
    return record

@router.put("/{item_id}", response_model=DataResponse, summary="데이터 수정")
def update_data_item(item_id: str, payload: DataUpdate):
    """
    지정한 ID의 매출 데이터를 수정합니다.
    """
    updated = firebase_service.update_data(item_id, payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="수정할 데이터를 찾을 수 없습니다.")
    return updated

@router.delete("/{item_id}", status_code=status.HTTP_200_OK, summary="데이터 삭제")
def delete_data_item(item_id: str):
    """
    지정한 ID의 매출 데이터를 삭제합니다.
    """
    success = firebase_service.delete_data(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="삭제할 데이터를 찾을 수 없습니다.")
    return {"message": "데이터가 성공적으로 삭제되었습니다.", "id": item_id}
