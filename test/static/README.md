# 존재하는 데이터 이용

## (필요시) 데이터 샘플링

아래 명령어를 프로젝트 최상단 경로에서 실행합니다.

```shell
uv run --env-file .env python -m test.static.0_sample_test_data
```

그 결과로 `test/static/sampled_test_data_%Y%m%d_%H%M%S.json`라는 이름의 데이터가 생성이 됩니다.

> ⚠️ **중요!** 이 데이터를 그대로 사용하는 것이 아니라 사용자가 검토한 후 수정해야 합니다. 아래는 샘플 데이터의 예시입니다.

```json
[
  {
    "question": "강시현 출연작 중에서 야기 류이치가 감독한 영화 이름과 러닝타임이 궁금해",
    "answer": "강시현 배우가 출연하고 야기 류이치가 감독한 영화는 '도라에몽: 스탠바이미 2'이며, 러닝타임은 1시간 35분입니다.",
    "difficulty": "hard"
  },
  {
    "question": "영화 이끼은 어떤 이야기를 담고 있나요",
    "answer": "영화 '이끼'는 아버지의 부고를 듣고 시골 마을을 찾은 '유해국(박해일)'이 마을 이장 '천용덕(정재영)'과 마을 사람들의 비밀을 파헤치는 이야기를 다룬 스릴러 영화입니다.\n\n자세한 줄거리는 다음과 같습니다...",
    "difficulty": "easy"
  }
  ...
]
```

## 1. Agent의 응답 추출

주어진 질의들에 대한 master agent의 응답을 생성합니다.

```shell
uv run --env-file .env python -m test.static.1_get_agent_result
```

그 결과로 `test/static/agent_results` 폴더에 `agent_result_%Y%m%d_%H%M%S.jsonl`라는 이름의 데이터가 생성이 됩니다.

```jsonl
{"question": "강시현 출연작 중에서 야기 류이치가 감독한 영화 이름과 러닝타임이 궁금해", "expected_answer": "강시현 배우가 출연하고 야기 류이치가 감독한 영화는 '도라에몽: 스탠바이미 2'이며, 러닝타임은 1시간 35분입니다.", "agent_response": "강시현 배우가 출연하고 야기 류이치 감독이 연출한 영화는 '도라에몽: 스탠바이미 2'이며, 러닝타임은 1시간 35분입니다.", "difficulty": "hard", "trace": [...]}
{"question": "영화 이끼은 어떤 이야기를 담고 있나요", "expected_answer": "영화 '이끼'는...", "agent_response": "영화 '이끼'는...", "difficulty": "easy", "trace": [...]}
...
```

## 2. Agent 응답 평가

생성된 응답에 대해 평가를 진행합니다.

```shell
uv run --env-file .env python -m test.static.2_evaluate_agent_result
```

그 결과로 `test/static/evaluation_results` 폴더에 `evaluation_result_%Y%m%d_%H%M%S.jsonl`라는 이름의 데이터가 생성이 됩니다.

```jsonl
{"question": "강시현 출연작 중에서 야기 류이치가 감독한 영화 이름과 러닝타임이 궁금해", "expected_answer": "강시현 배우가 출연하고 야기 류이치가 감독한 영화는 '도라에몽: 스탠바이미 2'이며, 러닝타임은 1시간 35분입니다.", "agent_response": "강시현 배우가 출연하고 야기 류이치 감독이 연출한 영화는 '도라에몽: 스탠바이미 2'이며, 러닝타임은 1시간 35분입니다.", "eval_response": {"explanation": "AI 모델의 답변이 질문에 대한 실제 정답과 완전히 일치합니다. 영화 이름과 러닝타임 정보가 정확하게 제공되었습니다.", "is_answer_correct": true}}
{"question": "영화 이끼은 어떤 이야기를 담고 있나요", "expected_answer": "영화 '이끼'는 ...", "agent_response": "영화 '이끼'는 ...", "eval_response": {"explanation": "AI 모델의 답변은 영화 '이끼'의 핵심 줄거리와 초기 전개를 정확하게 설명하고 있습니다. 실제 정답과 비교했을 때, 주인공 '해국'의 이름, 아버지의 죽음으로 인해 시골 마을을 찾게 되는 배경, 마을 사람들과 이장 '천용덕'에 대한 의심, 그리고 마을의 비밀을 파헤치는 스릴러라는 장르 설명 등 주요 내용이 일치합니다. 실제 정답이 영화의 전체적인 줄거리 흐름과 다루는 주제까지 언급하는 반면, AI 모델의 답변은 영화의 초반부 전개에 더 집중하여 설명하고 있습니다. 하지만 AI 답변의 내용은 모두 사실이며 질문에 대한 올바른 정보를 제공합니다. 따라서 'is_answer_correct'는 True로 판단합니다.", "is_answer_correct": true}}
...
```
