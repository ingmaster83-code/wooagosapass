"""
콘텐츠 없는 자격증 페이지에 시리즈/분야별 공통 콘텐츠를 stats JSON에 추가한다.
추가 후 generate_pages.py를 재실행하면 페이지에 반영된다.
"""
import json
import glob
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"

# ── 시리즈별 검정방법 템플릿 ──────────────────────────────────────────
SERIES_METHOD = {
    "기술사": {
        "exam_method": "- 필기 : 단답형 및 주관식 논술형 (매교시당 100분, 총 400분)\n- 면접 : 구술형 면접(30분 정도)",
        "exam_method_written": "단답형 및 주관식 논술형 (매교시당 100분, 총 400분)",
        "exam_method_prac": "구술형 면접 (30분 정도)",
        "written_criteria": "100점을 만점으로 하여 60점 이상",
        "prac_criteria": "100점을 만점으로 하여 60점 이상",
    },
    "기사": {
        "exam_method": "- 필기 : 객관식 4지 택일형, 과목당 20문항 (과목당 30분)\n- 실기 : 필답형 또는 작업형",
        "exam_method_written": "객관식 4지 택일형, 과목당 20문항 (과목당 30분)",
        "exam_method_prac": "필답형 또는 작업형",
        "written_criteria": "100점을 만점으로 하여 과목당 40점 이상이고 전 과목 평균 60점 이상",
        "prac_criteria": "100점을 만점으로 하여 60점 이상",
    },
    "산업기사": {
        "exam_method": "- 필기 : 객관식 4지 택일형, 과목당 20문항 (과목당 30분)\n- 실기 : 필답형 또는 작업형",
        "exam_method_written": "객관식 4지 택일형, 과목당 20문항 (과목당 30분)",
        "exam_method_prac": "필답형 또는 작업형",
        "written_criteria": "100점을 만점으로 하여 과목당 40점 이상이고 전 과목 평균 60점 이상",
        "prac_criteria": "100점을 만점으로 하여 60점 이상",
    },
    "기능사": {
        "exam_method": "- 필기 : 객관식 4지 택일형 (60문항, 60분)\n- 실기 : 작업형 (시험시간 표준시간 기준)",
        "exam_method_written": "객관식 4지 택일형 (60문항, 60분)",
        "exam_method_prac": "작업형 (시험시간 표준시간 기준)",
        "written_criteria": "100점을 만점으로 하여 60점 이상",
        "prac_criteria": "100점을 만점으로 하여 60점 이상",
    },
    "기능장": {
        "exam_method": "- 필기 : 객관식 4지 택일형 (60문항, 60분)\n- 실기 : 작업형 (시험시간 표준시간 기준)",
        "exam_method_written": "객관식 4지 택일형 (60문항, 60분)",
        "exam_method_prac": "작업형 (시험시간 표준시간 기준)",
        "written_criteria": "100점을 만점으로 하여 과목당 40점 이상이고 전 과목 평균 60점 이상",
        "prac_criteria": "100점을 만점으로 하여 60점 이상",
    },
}

# ── 시리즈별 출제경향 템플릿 (자격증명 치환용 {name}) ──────────────────
SERIES_TENDENCY = {
    "기술사": "{name} 시험은 해당 분야의 실무 경험, 일반지식, 전문지식 및 응용능력을 평가합니다. 또한 기술사로서의 경영관리 지도·감리 능력, 자질 및 품위를 평가합니다. 논술형으로 출제되므로 기본 원리 이해와 함께 실무 적용 능력을 키우는 것이 중요합니다.",
    "기사": "{name} 필기시험은 해당 직무에 필요한 공학적 기초지식과 전문이론을 평가합니다. 실기시험은 현장 실무 능력을 중심으로 출제됩니다. 최근 출제 경향은 현장 적용 능력과 이론의 실무 연계를 강조하는 방향으로 출제됩니다.",
    "산업기사": "{name} 필기시험은 해당 직무 수행에 필요한 기초 이론 및 실무 지식을 평가합니다. 실기시험은 실무 능력과 기능을 중심으로 평가됩니다. 기출문제를 충분히 반복 학습하고, 기본 개념과 계산 문제를 균형 있게 준비하는 것이 효과적입니다.",
    "기능사": "{name} 필기시험은 해당 직종의 기초 기술 이론과 실무 지식을 평가합니다. 실기시험은 실제 작업 수행 능력을 평가합니다. 기출문제 중심으로 학습하고 실기는 충분한 반복 연습이 필요합니다.",
    "기능장": "{name} 시험은 해당 분야 최고 수준의 숙련 기능을 평가합니다. 오랜 현장 경험을 바탕으로 한 전문적인 기능과 지식이 요구됩니다. 작업형 실기에서는 정밀도와 완성도를 집중적으로 평가합니다.",
}

# ── 분야별 응시자격 안내 ──────────────────────────────────────────────
SERIES_ELIGIBILITY = {
    "기술사": "기사 자격 취득 후 4년 이상 실무경력, 산업기사 취득 후 5년 이상 실무경력, 또는 해당 분야 기술사 자격 보유자가 응시할 수 있습니다. 학력에 따라 응시 자격이 다를 수 있으므로 큐넷에서 정확한 자격 요건을 확인하세요.",
    "기사": "관련학과 4년제 대학 졸업(예정)자, 3년제 전문대 졸업 후 1년 이상 실무경력, 2년제 전문대 졸업 후 2년 이상 실무경력, 또는 동일·유사 분야 산업기사 자격 취득 후 1년 이상 실무경력이 필요합니다.",
    "산업기사": "관련학과 전문대 졸업(예정)자, 기능사 자격 취득 후 1년 이상 실무경력, 또는 동일·유사 직무 분야 2년 이상 실무경력이 필요합니다. 학력 및 경력 요건에 대한 정확한 사항은 큐넷에서 확인하세요.",
    "기능사": "응시 자격에 제한이 없습니다. 연령, 학력, 경력에 관계없이 누구나 응시할 수 있습니다.",
    "기능장": "기사 또는 산업기사 자격 취득 후 해당 실무경력, 또는 기능사 자격 취득 후 5년 이상 실무경력이 있어야 합니다. 정확한 응시 자격은 큐넷(Q-Net)에서 확인하세요.",
}

# ── 특수 시리즈 처리 ─────────────────────────────────────────────────
SPECIAL_SERIES = {
    "청소년지도사": {
        "exam_method": "- 필기 : 객관식 (과목별 25문항, 과목별 40분)\n- 면접 : 개인 면접 (10분 내외)",
        "exam_method_written": "객관식 (과목별 25문항, 과목별 40분)",
        "exam_method_prac": "개인 면접 (10분 내외)",
        "written_criteria": "100점을 만점으로 하여 과목당 40점 이상이고 전 과목 평균 60점 이상",
        "prac_criteria": "합격·불합격 판정",
        "tendency": "청소년지도사 시험은 청소년 관련 법률, 청소년 심리, 청소년 프로그램 개발 및 평가 등 청소년 지도 실무에 필요한 지식을 평가합니다. 면접에서는 청소년 지도자로서의 자질과 직무 이해도를 평가합니다.",
        "eligibility": "1급은 2급 청소년지도사 취득 후 3년 이상 실무경력, 2급은 관련학과 대졸 또는 2년 이상 실무경력, 3급은 관련학과 전문대졸 또는 동일 분야 1년 이상 실무경력이 필요합니다.",
    },
    "청소년상담사": {
        "exam_method": "- 필기 : 객관식 (과목별 25문항, 과목별 40분)\n- 면접 : 개인 면접 (10분 내외)",
        "exam_method_written": "객관식 (과목별 25문항, 과목별 40분)",
        "exam_method_prac": "개인 면접 (10분 내외)",
        "written_criteria": "100점을 만점으로 하여 과목당 40점 이상이고 전 과목 평균 60점 이상",
        "prac_criteria": "합격·불합격 판정",
        "tendency": "청소년상담사 시험은 발달심리, 집단상담, 가족상담, 특수상담, 학습이론 등 청소년 상담 분야의 전문 지식을 평가합니다. 면접에서는 상담자로서의 자질과 윤리 의식을 평가합니다.",
        "eligibility": "1급은 2급 청소년상담사 취득 후 3년 이상 실무경력, 2급은 관련학과 대졸 이상 학력 및 상담 실습, 3급은 전문대졸 이상 학력 및 실습 조건을 충족해야 합니다.",
    },
    "공인노무사": {
        "exam_method": "- 1차 : 객관식 (5지 택일형, 과목당 40문항)\n- 2차 : 주관식 논술형 (4문항 이상)\n- 3차 : 면접",
        "exam_method_written": "1차 객관식 (5지 택일형, 과목당 40문항) / 2차 주관식 논술형",
        "exam_method_prac": "3차 면접",
        "written_criteria": "1차: 100점 만점, 과목당 40점 이상, 평균 60점 이상 / 2차: 100점 만점, 과목당 40점 이상, 평균 60점 이상",
        "prac_criteria": "합격·불합격 판정",
        "tendency": "공인노무사 시험은 노동법, 노동경제학, 사회보험법, 경영조직론 등 노무 전문가에게 필요한 법률적·경제적 지식을 평가합니다. 2차 시험은 노동관계법령 적용 능력과 분석력을 평가합니다.",
        "eligibility": "학력·경력 제한 없이 누구나 응시 가능합니다. 단 결격사유(금치산자, 파산선고자, 금고 이상 형 집행 중인 자 등)에 해당하면 응시가 제한됩니다.",
    },
    "공인중개사": {
        "exam_method": "- 1차 : 객관식 4지 택일형 (과목당 40문항, 과목당 50분)\n- 2차 : 객관식 5지 택일형 (과목당 40문항, 과목당 50분)",
        "exam_method_written": "1차·2차 모두 객관식 (과목당 40문항, 과목당 50분)",
        "exam_method_prac": None,
        "written_criteria": "100점을 만점으로 하여 과목당 40점 이상이고 전 과목 평균 60점 이상",
        "prac_criteria": None,
        "tendency": "공인중개사 시험은 민법 및 민사특별법, 부동산학개론, 공인중개사법령, 부동산공시법령, 부동산세법 등을 평가합니다. 법령 개정사항을 반영한 최신 기출문제 분석이 중요합니다.",
        "eligibility": "학력·경력 제한 없이 누구나 응시 가능합니다. 단 공인중개사법에 따른 결격사유에 해당하지 않아야 합니다.",
    },
    "관광통역안내사": {
        "exam_method": "- 1차 : 객관식 4지 택일형 (과목당 25문항)\n- 2차 : 국어(외국어) 면접",
        "exam_method_written": "객관식 4지 택일형 (과목당 25문항)",
        "exam_method_prac": "외국어 구술 면접",
        "written_criteria": "100점을 만점으로 하여 과목당 40점 이상이고 전 과목 평균 60점 이상",
        "prac_criteria": "합격·불합격 판정",
        "tendency": "관광통역안내사 시험은 관광자원해설, 관광법규, 관광학개론, 외국어(영·일·중·불·독·스·러·아 등) 과목으로 구성됩니다. 면접에서는 해당 외국어 구사 능력과 관광 안내 실무 능력을 평가합니다.",
        "eligibility": "학력·경력 제한 없이 누구나 응시 가능합니다.",
    },
    "경매사": {
        "exam_method": "- 필기 : 객관식 4지 택일형\n- 실기 : 구술형 면접 또는 필답형",
        "exam_method_written": "객관식 4지 택일형",
        "exam_method_prac": "구술형 면접 또는 필답형",
        "written_criteria": "100점을 만점으로 하여 과목당 40점 이상이고 전 과목 평균 60점 이상",
        "prac_criteria": "100점을 만점으로 하여 60점 이상",
        "tendency": "경매사 시험은 경매 관련 법규, 농수산물 유통·가격 안정에 관한 법률, 농산물 품질 관리, 경매 실무 등을 평가합니다.",
        "eligibility": "학력 제한은 없으나 해당 경매사 종류에 따라 관련 경력이 필요할 수 있습니다. 정확한 응시 자격은 큐넷에서 확인하세요.",
    },
    "행정사": {
        "exam_method": "- 1차 : 객관식 5지 택일형 (과목당 40문항)\n- 2차 : 주관식 논술형 및 기입형",
        "exam_method_written": "1차 객관식 / 2차 주관식 논술형·기입형",
        "exam_method_prac": None,
        "written_criteria": "1차: 100점 만점, 과목당 40점 이상, 평균 60점 이상 / 2차: 100점 만점, 과목당 40점 이상, 평균 60점 이상",
        "prac_criteria": None,
        "tendency": "행정사 시험은 민법(계약), 행정법, 행정학, 민사소송법 등 행정 업무 처리에 필요한 법률 지식을 평가합니다. 2차에서는 법령 적용 능력과 서류 작성 능력을 평가합니다.",
        "eligibility": "학력·경력 제한 없이 누구나 응시 가능합니다. 단 행정사법에 따른 결격사유에 해당하지 않아야 합니다.",
    },
    "경영지도사": {
        "exam_method": "- 1차 : 객관식 4지 택일형\n- 2차 : 주관식 논술형",
        "exam_method_written": "1차 객관식 / 2차 주관식 논술형",
        "exam_method_prac": None,
        "written_criteria": "100점을 만점으로 하여 과목당 40점 이상이고 전 과목 평균 60점 이상",
        "prac_criteria": None,
        "tendency": "경영지도사 시험은 경영학, 경제학, 회계학 등 기업 경영 전반에 걸친 전문 지식을 평가합니다. 2차는 인적자원관리, 재무관리, 마케팅, 생산관리 등 세부 분야별 논술 능력을 평가합니다.",
        "eligibility": "학력·경력 제한 없이 누구나 응시 가능합니다.",
    },
    "국가유산수리기능자": {
        "exam_method": "- 이론 : 구술형 면접\n- 실기 : 작업형",
        "exam_method_written": "구술형 면접 (이론)",
        "exam_method_prac": "작업형 실기",
        "written_criteria": "합격·불합격 판정",
        "prac_criteria": "합격·불합격 판정",
        "tendency": "국가유산수리기능자 시험은 문화재 수리 분야의 전통 기술과 재료에 대한 이해를 평가합니다. 실기는 실제 전통 기법에 따른 수리 작업 능력을 중심으로 평가합니다.",
        "eligibility": "해당 분야 실무 경력이 필요합니다. 종목에 따라 경력 요건이 다르므로 국가유산진흥원에서 정확한 자격 요건을 확인하세요.",
    },
    "국가유산수리기술자": {
        "exam_method": "- 필기 : 객관식 및 주관식\n- 실기 : 작업형 또는 구술형",
        "exam_method_written": "객관식 및 주관식",
        "exam_method_prac": "작업형 또는 구술형",
        "written_criteria": "100점을 만점으로 하여 60점 이상",
        "prac_criteria": "합격·불합격 판정",
        "tendency": "국가유산수리기술자 시험은 문화재 보존·복원·수리에 필요한 전문 기술 이론 및 실무 능력을 평가합니다. 전통 건축 양식, 재료 특성, 수리 기법 등에 대한 깊은 이해가 요구됩니다.",
        "eligibility": "해당 분야 실무 경력 요건을 충족해야 합니다. 정확한 응시 자격은 국가유산진흥원에서 확인하세요.",
    },
    "정수시설운영관리사": {
        "exam_method": "- 필기 : 객관식 4지 택일형 (과목당 20문항)\n- 실기 : 필답형",
        "exam_method_written": "객관식 4지 택일형 (과목당 20문항)",
        "exam_method_prac": "필답형",
        "written_criteria": "100점을 만점으로 하여 과목당 40점 이상이고 전 과목 평균 60점 이상",
        "prac_criteria": "100점을 만점으로 하여 60점 이상",
        "tendency": "정수시설운영관리사 시험은 수질관리, 정수처리, 전기·기계 설비 운영, 수질오염공정시험기준 등 정수장 운영 실무 전반을 평가합니다.",
        "eligibility": "정수 관련 분야의 학력 또는 실무 경력이 필요합니다. 등급에 따라 자격 요건이 다릅니다.",
    },
    "경비지도사": {
        "exam_method": "- 1차 : 객관식 4지 택일형\n- 2차 : 객관식 4지 택일형",
        "exam_method_written": "1차·2차 모두 객관식 4지 택일형",
        "exam_method_prac": None,
        "written_criteria": "100점을 만점으로 하여 과목당 40점 이상이고 전 과목 평균 60점 이상",
        "prac_criteria": None,
        "tendency": "경비지도사 시험은 경비업법, 범죄학, 경호학, 시설경비론 등 경비 분야의 법적·실무적 지식을 평가합니다.",
        "eligibility": "학력·경력 제한 없이 누구나 응시 가능합니다. 단 경비업법에 따른 결격사유에 해당하지 않아야 합니다.",
    },
    "산업안전지도사": {
        "exam_method": "- 1차 : 객관식 4지 택일형\n- 2차 : 주관식 논술형\n- 3차 : 면접",
        "exam_method_written": "1차 객관식 / 2차 주관식 논술형",
        "exam_method_prac": "3차 면접",
        "written_criteria": "1차·2차: 100점 만점, 과목당 40점 이상, 평균 60점 이상",
        "prac_criteria": "합격·불합격 판정",
        "tendency": "산업안전지도사 시험은 산업안전보건법, 기계·화공·전기 안전 이론, 위험성 평가, 사고 조사 등을 평가합니다. 현장 적용 능력과 법령 이해가 중요합니다.",
        "eligibility": "학력·경력 제한 없이 누구나 응시 가능합니다.",
    },
    "산업보건지도사": {
        "exam_method": "- 1차 : 객관식 4지 택일형\n- 2차 : 주관식 논술형\n- 3차 : 면접",
        "exam_method_written": "1차 객관식 / 2차 주관식 논술형",
        "exam_method_prac": "3차 면접",
        "written_criteria": "1차·2차: 100점 만점, 과목당 40점 이상, 평균 60점 이상",
        "prac_criteria": "합격·불합격 판정",
        "tendency": "산업보건지도사 시험은 직업환경의학, 작업환경측정, 근골격계질환 예방, 산업위생 관리 등을 평가합니다.",
        "eligibility": "학력·경력 제한 없이 누구나 응시 가능합니다.",
    },
    "기술지도사": {
        "exam_method": "- 1차 : 객관식 4지 택일형\n- 2차 : 주관식 논술형",
        "exam_method_written": "1차 객관식 / 2차 주관식 논술형",
        "exam_method_prac": None,
        "written_criteria": "100점을 만점으로 하여 과목당 40점 이상이고 전 과목 평균 60점 이상",
        "prac_criteria": None,
        "tendency": "기술지도사 시험은 해당 기술 분야의 전문 이론 및 기업 기술 지도 능력을 평가합니다.",
        "eligibility": "해당 분야 기사 이상 자격증 보유 또는 관련 학위 소지자 등 일정 자격을 갖춰야 합니다.",
    },
}

# ── 분야별 학과 정보 ─────────────────────────────────────────────────
FIELD_DEPT = {
    "건설": "대학의 건축공학, 토목공학, 도시공학, 환경공학 등 관련 학과",
    "기계": "대학의 기계공학, 자동차공학, 항공공학, 메카트로닉스공학 등 관련 학과",
    "전기.전자": "대학의 전기공학, 전자공학, 제어공학, 정보통신공학 등 관련 학과",
    "정보통신": "대학의 컴퓨터공학, 정보통신공학, 소프트웨어공학, 전자공학 등 관련 학과",
    "안전관리": "대학의 안전공학, 소방학, 산업공학, 환경공학 등 관련 학과",
    "환경.에너지": "대학의 환경공학, 에너지공학, 화학공학, 대기환경공학 등 관련 학과",
    "화학": "대학의 화학공학, 화학, 신소재공학, 고분자공학 등 관련 학과",
    "재료": "대학의 금속공학, 재료공학, 신소재공학, 세라믹공학 등 관련 학과",
    "농림어업": "대학의 농학, 임학, 수산학, 식품공학 등 관련 학과",
    "식품.가공": "대학의 식품공학, 식품영양학, 조리학, 제과제빵학 등 관련 학과",
    "경영.회계.사무": "대학의 경영학, 회계학, 행정학, 무역학 등 관련 학과",
    "섬유.의복": "대학의 섬유공학, 의류학, 패션디자인학, 생활과학 등 관련 학과",
    "인쇄.목재.가구.공예": "대학의 목재공학, 공예학, 산업디자인학, 인쇄공학 등 관련 학과",
    "음식서비스": "대학의 조리학, 식품영양학, 호텔외식경영학, 관광학 등 관련 학과",
    "문화.예술.디자인.방송": "대학의 디자인학, 예술학, 방송미디어학, 영상학 등 관련 학과",
    "이용.숙박.여행.오락.스포츠": "대학의 관광학, 호텔경영학, 스포츠과학, 레저스포츠학 등 관련 학과",
    "광업자원": "대학의 자원공학, 지질학, 광산공학, 에너지자원공학 등 관련 학과",
    "보건.의료": "대학의 간호학, 보건학, 의료기술학, 임상병리학 등 관련 학과",
    "운전.운송": "운전 관련 학과 또는 직업훈련기관",
}


def build_exam_info(name: str, series: str, field: str) -> dict:
    """시리즈와 분야를 기반으로 exam_info dict 생성"""
    result = {}

    # 특수 시리즈 우선 처리
    special = SPECIAL_SERIES.get(series)
    if special:
        result["exam_method"] = special["exam_method"]
        result["exam_method_written"] = special.get("exam_method_written", "")
        result["exam_method_prac"] = special.get("exam_method_prac", "")
        result["written_criteria"] = special.get("written_criteria", "")
        result["prac_criteria"] = special.get("prac_criteria", "")
        result["tendency"] = special.get("tendency", "").replace("{name}", name)
        result["eligibility"] = special.get("eligibility", "")
        dept = FIELD_DEPT.get(field, "관련 학과")
        result["related_dept"] = dept
        return result

    # 일반 시리즈
    method = SERIES_METHOD.get(series)
    if method:
        result["exam_method"] = method["exam_method"]
        result["exam_method_written"] = method["exam_method_written"]
        result["exam_method_prac"] = method["exam_method_prac"]
        result["written_criteria"] = method["written_criteria"]
        result["prac_criteria"] = method["prac_criteria"]

    tendency_tpl = SERIES_TENDENCY.get(series)
    if tendency_tpl:
        result["tendency"] = tendency_tpl.replace("{name}", name)

    eligibility = SERIES_ELIGIBILITY.get(series)
    if eligibility:
        result["eligibility"] = eligibility

    dept = FIELD_DEPT.get(field, "관련 학과")
    result["related_dept"] = dept

    return result


def build_info_list(name: str, series: str, field: str) -> list:
    """취득방법 content 문자열을 생성해 info 리스트로 반환"""
    lines = []

    dept = FIELD_DEPT.get(field, "관련 학과")
    method = SERIES_METHOD.get(series, SPECIAL_SERIES.get(series, {}))
    eligibility = SERIES_ELIGIBILITY.get(series, "")

    lines.append(f"① 시 행 처 : 한국산업인력공단")
    if dept:
        lines.append(f"② 관련학과 : {dept}")

    # 시험과목은 자격증별로 다르므로 일반 안내로 대체
    m_written = method.get("exam_method_written", "")
    m_prac = method.get("exam_method_prac", "")
    if m_written or m_prac:
        lines.append(f"④ 검정방법")
        if m_written:
            lines.append(f"   - 필기 : {m_written}")
        if m_prac:
            lines.append(f"   - 실기 : {m_prac}")

    w_crit = method.get("written_criteria", "")
    p_crit = method.get("prac_criteria", "")
    if w_crit or p_crit:
        lines.append(f"⑤ 합격기준")
        if w_crit:
            lines.append(f"   - 필기 : {w_crit}")
        if p_crit:
            lines.append(f"   - 실기 : {p_crit}")

    content = "\n".join(lines)

    tendency_tpl = SERIES_TENDENCY.get(series, "")
    tendency = tendency_tpl.replace("{name}", name) if tendency_tpl else ""
    if series in SPECIAL_SERIES:
        tendency = SPECIAL_SERIES[series].get("tendency", "").replace("{name}", name)

    result = []
    if tendency:
        result.append({"type": "출제경향", "content": tendency})
    if content:
        result.append({"type": "취득방법", "content": content})
    return result


def main():
    files = sorted(DATA_DIR.glob("stats/*.json"))
    updated = 0
    skipped = 0

    for f in files:
        d = json.loads(f.read_text(encoding="utf-8"))
        name = d.get("name", "")
        series = d.get("series", "")
        field = d.get("field", "")

        # 이미 info가 충분히 있으면 건너뜀
        info = d.get("info", [])
        has_method = any(
            i.get("type") == "취득방법" and len(i.get("content", "")) > 50
            for i in info
        )
        has_tendency = any(
            i.get("type") == "출제경향" and len(i.get("content", "")) > 30
            for i in info
        )
        if has_method and has_tendency:
            skipped += 1
            continue

        # 새 info 생성
        new_info = build_info_list(name, series, field)
        if not new_info:
            skipped += 1
            continue

        # 기존 info에 없는 타입만 추가
        existing_types = {i["type"] for i in info}
        for item in new_info:
            if item["type"] not in existing_types:
                info.append(item)

        d["info"] = info
        f.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        updated += 1

    print(f"완료: {updated}개 업데이트, {skipped}개 스킵")


if __name__ == "__main__":
    main()
