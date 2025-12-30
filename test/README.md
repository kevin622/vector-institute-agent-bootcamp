# Agent를 테스트하는 방법

## 1. 질의 데이터 생성

아래 명령어를 프로젝트 최상단 경로에서 실행합니다.

```shell
uv run --env-file .env python -m test.gen.1_synthesize_data
```

그 결과로 `test/gen/synthesized_data` 폴더에 `synthesized_queries_%Y%m%d_%H%M%S`라는 이름의 데이터가 생성이 됩니다.

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
uv run --env-file .env python -m test.gen.2_1_get_agent_result_from_scratch
```

그 결과로 `test/gen/agent_results_from_scratch` 폴더에 `agent_result_%Y%m%d_%H%M%S`라는 이름의 데이터가 생성이 됩니다.

```jsonl
{"query": "데이터베이스에 있는 테이블들의 이름을 전부 알려줘.", "agent_response": "데이터베이스에는 'clients', 'contracts', 'departments', 'employees', 'invoices', 'meetings', 'products', 'project_assignments', 'projects' 테이블들이 있습니다.", "difficulty": "simple", "trace": [...]}
{"query": "요즘 제일 인기있는 K-POP 아이돌 그룹은 어디야?", "agent_response": "현재 가장 인기 있는 K-POP 아이돌 그룹은 다양한 기준에 따라 다릅니다. 최신 정보를 종합해 볼 때, 다음과 같은 그룹들이 큰 인기를 얻고 있습니다.\n\n*   **글로벌 인기:** **BTS**와 **블랙핑크**는 전 세계적으로 여전히 가장 강력한 영향력을 보여주고 있습니다.\n*...", "difficulty": "simple", "trace": [...]}
...
```

### 2-2. master agent에 질의를 입력으로 하여 예측 생성

이미 답이 생성되어있는 데이터에 대해 한 번 더 답을 생성합니다.

```shell
uv run --env-file .env python -m test.gen.2_2_get_agent_result_to_compare
```

그 결과로 `test/gen/agent_results_to_compare` 폴더에 `agent_result_%Y%m%d_%H%M%S`라는 이름의 데이터가 생성이 됩니다.

```jsonl
{"query": "데이터베이스에 있는 테이블들의 이름을 전부 알려줘.", "agent_response": "데이터베이스에는 'clients', 'contracts', 'departments', 'employees', 'invoices', 'meetings', 'products', 'project_assignments', 'projects' 테이블들이 있습니다.", "new_agent_response": "데이터베이스에 있는 테이블은 clients, contracts, departments, employees, invoices, meetings, products, project_assignments, projects 입니다.", "difficulty": "simple", "trace": [], "new_trace": []}
{"query": "요즘 제일 인기있는 K-POP 아이돌 그룹은 어디야?", "agent_response": "현재 가장 인기 있는 K-POP 아이돌 그룹은 다양한 기준에 따라 다릅니다. 최신 정보를 종합해 볼 때, 다음과 같은 그룹들이 큰 인기를 얻고 있습니다.\n\n*   **글로벌 인기:** **BTS**와 **블랙핑크**는 전 세계적으로 여전히 가장 강력한 영향력을 보여주고 있습니다.\n*...", "new_agent_response": "요즘 가장 인기 있는 K-POP 아이돌 그룹은 다음과 같습니다.\n\n*   **세븐틴 (SEVENTEEN)**\n*   **스트레이 키즈 (Stray Kids)**\n*   **뉴진스 (NewJeans)**\n*...", "difficulty": "simple", "trace": [], "new_trace": []}
```

## 3. 생성된 정답을 평가

[2-2](#2-2-master-agent에-질의를-입력으로-하여-예측-생성)를 통해 생성된 두 답을 LLM Judge를 통해 비교합니다.

```shell
uv run --env-file .env python -m test.gen.3_eval_agent_result
```

그 결과로 `test/gen/evaluation_results` 폴더에 `evaluation_result_%Y%m%d_%H%M%S`라는 이름의 데이터가 생성이 됩니다.

```jsonl
{"query": "데이터베이스에 있는 테이블들의 이름을 전부 알려줘.", "expected_answer": "데이터베이스에는 'clients', 'contracts', 'departments', 'employees', 'invoices', 'meetings', 'products', 'project_assignments', 'projects' 테이블들이 있습니다.", "agent_response": "데이터베이스에 있는 테이블은 clients, contracts, departments, employees, invoices, meetings, products, project_assignments, projects 입니다.", "evaluator_explanation": {"explanation": "AI 모델의 답변은 실제 정답과 동일하게 데이터베이스의 모든 테이블 이름을 정확하게 나열했습니다.", "is_answer_correct": true}}
{"query": "요즘 제일 인기있는 K-POP 아이돌 그룹은 어디야?", "expected_answer": "현재 가장 인기 있는 K-POP 아이돌 그룹은 다양한 기준에 따라 다릅니다. 최신 정보를...", "agent_response": "요즘 가장 인기 있는 K-POP 아이돌 그룹은 다음과 같습니다.\n\n*...", "evaluator_explanation": {"explanation": "AI 모델의 답변은 질문에 대한 직접적인 답변으로...", "is_answer_correct": true}}
```
