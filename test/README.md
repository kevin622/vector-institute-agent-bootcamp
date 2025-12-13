# Agent를 테스트하는 방법

## 1. 질의 데이터 생성

아래 명령어를 프로젝트 최상단 경로에서 실행합니다.

```shell
uv run --env-file .env python -m test.1_synthesize_data
```

그 결과로 `test/synthesized_data` 폴더에 `synthesized_queries_%Y%m%d_%H%M%S`라는 이름의 데이터가 생성이 됩니다.

```json
{
    "result": [
        {
            "query": "데이터베이스에 있는 테이블들의 이름을 전부 알려줘.",
            "difficulty": "simple"
        },
        {
            "query": "요즘 제일 인기있는 K-POP 아이돌 그룹은 어디야?",
            "difficulty": "simple"
        },
        ...
    ]
}
```

## 2. agent의 응답 추출

### 2-1. master agent에 질의를 입력으로 하여 정답 생성

생성된 질의들에 대한 master agent의 응답을 생성합니다.

```shell
uv run --env-file .env python -m test.2_1_get_agent_result_from_scratch
```

그 결과로 `test/agent_results_from_scratch` 폴더에 `agent_result_%Y%m%d_%H%M%S`라는 이름의 데이터가 생성이 됩니다.

```jsonl
{"query": "데이터베이스에 있는 테이블들의 이름을 전부 알려줘.", "agent_response": "데이터베이스에는 'clients', 'contracts', 'departments', 'employees', 'invoices', 'meetings', 'products', 'project_assignments', 'projects' 테이블들이 있습니다.", "difficulty": "simple", "trace": [...]}
{"query": "요즘 제일 인기있는 K-POP 아이돌 그룹은 어디야?", "agent_response": "현재 가장 인기 있는 K-POP 아이돌 그룹은 다양한 기준에 따라 다릅니다. 최신 정보를 종합해 볼 때, 다음과 같은 그룹들이 큰 인기를 얻고 있습니다.\n\n*   **글로벌 인기:** **BTS**와 **블랙핑크**는 전 세계적으로 여전히 가장 강력한 영향력을 보여주고 있습니다.\n*   **최근 차트 및 트렌드:** **화사, 라이즈, 에스파, TWICE, NMIXX, Stray Kids, ATEEZ, SEVENTEEN, ITZY, ENHYPEN** 등이 각종 차트 상위권을 차지하며 좋은 성적을 보여주고 있습니다.\n*   **걸그룹 브랜드 평판:** **블랙핑크**와 **뉴진스**가 높은 브랜드 평판을 유지하고 있습니다.\n\n이처럼 어떤 기준을 적용하느냐에 따라 인기 순위는 달라질 수 있습니다. 특별히 선호하는 기준이 있으시면 더 자세한 정보를 찾아드릴 수 있습니다.", "difficulty": "simple", "trace": [...]}
...
```

### 2-2. master agent에 질의를 입력으로 하여 예측 생성

이미 답이 생성되어있는 데이터에 대해 한 번 더 답을 생성합니다.

```shell
uv run --env-file .env python -m test.2_2_get_agent_result_to_compare
```

그 결과로 `test/agent_results_to_compare` 폴더에 `agent_result_%Y%m%d_%H%M%S`라는 이름의 데이터가 생성이 됩니다.

```jsonl
{"query": "데이터베이스에 있는 테이블들의 이름을 전부 알려줘.", "agent_response": "데이터베이스에는 'clients', 'contracts', 'departments', 'employees', 'invoices', 'meetings', 'products', 'project_assignments', 'projects' 테이블들이 있습니다.", "new_agent_response": "데이터베이스에 있는 테이블은 clients, contracts, departments, employees, invoices, meetings, products, project_assignments, projects 입니다.", "difficulty": "simple", "trace": [], "new_trace": []}
{"query": "요즘 제일 인기있는 K-POP 아이돌 그룹은 어디야?", "agent_response": "현재 가장 인기 있는 K-POP 아이돌 그룹은 다양한 기준에 따라 다릅니다. 최신 정보를 종합해 볼 때, 다음과 같은 그룹들이 큰 인기를 얻고 있습니다.\n\n*   **글로벌 인기:** **BTS**와 **블랙핑크**는 전 세계적으로 여전히 가장 강력한 영향력을 보여주고 있습니다.\n*   **최근 차트 및 트렌드:** **화사, 라이즈, 에스파, TWICE, NMIXX, Stray Kids, ATEEZ, SEVENTEEN, ITZY, ENHYPEN** 등이 각종 차트 상위권을 차지하며 좋은 성적을 보여주고 있습니다.\n*   **걸그룹 브랜드 평판:** **블랙핑크**와 **뉴진스**가 높은 브랜드 평판을 유지하고 있습니다.\n\n이처럼 어떤 기준을 적용하느냐에 따라 인기 순위는 달라질 수 있습니다. 특별히 선호하는 기준이 있으시면 더 자세한 정보를 찾아드릴 수 있습니다.", "new_agent_response": "요즘 가장 인기 있는 K-POP 아이돌 그룹은 다음과 같습니다.\n\n*   **세븐틴 (SEVENTEEN)**\n*   **스트레이 키즈 (Stray Kids)**\n*   **뉴진스 (NewJeans)**\n*   **투모로우바이투게더 (TOMORROW X TOGETHER)**\n*   **방탄소년단 (BTS)**\n*   **블랙핑크 (BLACKPINK)**\n*   **베이비몬스터 (BABYMONSTER)**\n\n이 그룹들은 IFPI(국제 음반 산업 협회) 글로벌 아티스트 차트나 K-POP 레이더와 같은 주요 차트에서 상위권을 차지하며 높은 인기를 보여주고 있습니다.", "difficulty": "simple", "trace": [], "new_trace": []}
```

## 3. 생성된 정답을 평가

[2-2](#2-2-master-agent에-질의를-입력으로-하여-예측-생성)를 통해 생성된 두 답을 LLM Judge를 통해 비교합니다.

```shell
uv run --env-file .env python -m test.3_eval_agent_result
```

그 결과로 `test/evaluation_results` 폴더에 `evaluation_result_%Y%m%d_%H%M%S`라는 이름의 데이터가 생성이 됩니다.

```jsonl
{"query": "데이터베이스에 있는 테이블들의 이름을 전부 알려줘.", "expected_answer": "데이터베이스에는 'clients', 'contracts', 'departments', 'employees', 'invoices', 'meetings', 'products', 'project_assignments', 'projects' 테이블들이 있습니다.", "agent_response": "데이터베이스에 있는 테이블은 clients, contracts, departments, employees, invoices, meetings, products, project_assignments, projects 입니다.", "evaluator_explanation": {"explanation": "AI 모델의 답변은 실제 정답과 동일하게 데이터베이스의 모든 테이블 이름을 정확하게 나열했습니다.", "is_answer_correct": true}}
{"query": "요즘 제일 인기있는 K-POP 아이돌 그룹은 어디야?", "expected_answer": "현재 가장 인기 있는 K-POP 아이돌 그룹은 다양한 기준에 따라 다릅니다. 최신 정보를 종합해 볼 때, 다음과 같은 그룹들이 큰 인기를 얻고 있습니다.\n\n*   **글로벌 인기:** **BTS**와 **블랙핑크**는 전 세계적으로 여전히 가장 강력한 영향력을 보여주고 있습니다.\n*   **최근 차트 및 트렌드:** **화사, 라이즈, 에스파, TWICE, NMIXX, Stray Kids, ATEEZ, SEVENTEEN, ITZY, ENHYPEN** 등이 각종 차트 상위권을 차지하며 좋은 성적을 보여주고 있습니다.\n*   **걸그룹 브랜드 평판:** **블랙핑크**와 **뉴진스**가 높은 브랜드 평판을 유지하고 있습니다.\n\n이처럼 어떤 기준을 적용하느냐에 따라 인기 순위는 달라질 수 있습니다. 특별히 선호하는 기준이 있으시면 더 자세한 정보를 찾아드릴 수 있습니다.", "agent_response": "요즘 가장 인기 있는 K-POP 아이돌 그룹은 다음과 같습니다.\n\n*   **세븐틴 (SEVENTEEN)**\n*   **스트레이 키즈 (Stray Kids)**\n*   **뉴진스 (NewJeans)**\n*   **투모로우바이투게더 (TOMORROW X TOGETHER)**\n*   **방탄소년단 (BTS)**\n*   **블랙핑크 (BLACKPINK)**\n*   **베이비몬스터 (BABYMONSTER)**\n\n이 그룹들은 IFPI(국제 음반 산업 협회) 글로벌 아티스트 차트나 K-POP 레이더와 같은 주요 차트에서 상위권을 차지하며 높은 인기를 보여주고 있습니다.", "evaluator_explanation": {"explanation": "AI 모델의 답변은 질문에 대한 직접적인 답변으로 현재 인기 있는 K-POP 아이돌 그룹의 목록을 제공합니다. 제시된 그룹들(세븐틴, 스트레이 키즈, 뉴진스, 투모로우바이투게더, 방탄소년단, 블랙핑크, 베이비몬스터)은 실제로 높은 인기를 얻고 있는 그룹들이며, 언급된 차트 지표(IFPI 글로벌 아티스트 차트, K-POP 레이더)는 인기 기준의 타당성을 뒷받침합니다. 그러나 '가장 인기 있는'이라는 질문의 특성상 다양한 기준에 따라 결과가 달라질 수 있음을 실제 정답처럼 명확하게 설명하지는 못했습니다. 또한, 실제 정답이 글로벌 인기, 최근 차트 및 트렌드, 걸그룹 브랜드 평판 등 세분화된 기준에 따라 더 광범위한 인기 그룹 목록을 제시한 것에 비해 AI 답변은 상대적으로 제한적인 목록을 제공했습니다. 예를 들어, 실제 정답에서 언급된 에스파, TWICE, NMIXX, ATEEZ, ENHYPEN 등이 AI 답변에는 포함되지 않았습니다. 따라서 AI 모델의 답변은 제시된 정보 자체는 정확하지만, 질문에 대한 포괄성 및 상세도 측면에서 실제 정답보다 부족합니다.", "is_answer_correct": true}}
```
