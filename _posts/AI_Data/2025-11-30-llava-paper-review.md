---
title: "[논문] Visual Instruction Tuning 리뷰 (LLaVA: Large Language and Vision Assistant)"
date: 2025-11-30 10:52:00 +0900
categories: [Paper Review]
tags: [논문리뷰, LLaVA, CLIP, Vicuna, LLaMA, Multimodal]
permalink: /paper-review/llava/
header:
  teaser: /assets/images/posts/llava-paper-review/01.png
---

수업에서 LLaVA 모델을 사용해보고자 해서 논문을 읽어보았다.

해당 포스트에서는 LLaVA 모델이 제시된 논문 "Visual Instruction Tuning"의 내용을 정리하며 LLaVA 모델의 구성과 학습 과정에 대해 정리하고자 한다. 모델을 구성하는 데에 사용된 다른 논문도 설명하고자 한다.

해당 논문은 두 가지 파트로 나누어 볼 수 있다.

1) 학습을 위해 지시문 데이터셋을 어떻게 수집했는지와 2) LLaVA 모델에서 이미지 인코더와 언어 모델을 어떻게 연결하였는지 를 기준으로 정리해보겠다.

#### LLaVA 모델 구성

![LLaVA 모델 구성]({{ "/assets/images/posts/llava-paper-review/01.png" | relative_url }})

LLaVA 모델 구성은 다음과 같다. 1) 비전 인코더 2) 선형 프로젝션 레이어 3) 언어 모델로 구성되고, 1) 비전 인코더와 3) 언어 모델 사이를 2) 선형 프로젝션 레이어가 잇는 형태이다. LLaVA 모델의 input으로 이미지와 언어 지시문이 들어가고, output으로 언어 응답이 나온다.

비전 인코더로는 OpenAI가 개발한 CLIP 모델의 이미지 인코더를 사용했고, 언어 모델로는 Meta가 개발한 LLaMA를 파인튜닝한 모델인 Vicuna를 사용했다. 자세한 설명은 이어서 진행한다.

#### LLaVA 내부 모델 연결 방법

LLaVA에서는 두 모델을 합친 형태로 되어있는데, 두 모델을 연결하는 방법이 논문 내용의 핵심 중 하나이다. 이미지 인코더가 뱉은 이미지 특성 벡터는 언어 모델이 이해할 수 없는 형식으로 되어있다. 언어 모델이 사용하는 벡터와 차원이 다르기 때문이다. 이들은 단순히 선형 매핑하는 형식을 도입해 두 모델을 연결했다.

![선형 투영 수식]({{ "/assets/images/posts/llava-paper-review/02.png" | relative_url }})

선형 벡터 W를 투영하여 이미지 인코더가 뱉은 이미지 특성 백터 Z_v를 H_v로 변환한다.

#### LLaVA 모델 상세 구조

이렇게 보았을 때는 대충 input과 output이 어떻게 되는지는 이해가 됐지만, 어떤 식으로 나오길래 중간에 선형 투영 레이어를 넣어야하는지, 그래서 어떻게 output이 나오는지 전혀 와닿지 않았다. 그래서 LLaVA 모델을 구성한 CLIP 모델과 Vicuna 모델을 함께 살펴보았다.

**CLIP**

![CLIP 학습 과정]({{ "/assets/images/posts/llava-paper-review/03.svg" | relative_url }})

![CLIP 분류 과정]({{ "/assets/images/posts/llava-paper-review/04.svg" | relative_url }})

Clip 모델은 "이미지와 가장 유사한 문장이 무엇인가"를 찾는 모델이다. 오픈AI가 개발한 모델로, 이미지와 텍스트를 같은 공간 상에 두어 유사도를 계산하는 방식이다. 모델 input으로 이미지와 문장을 입력하면, 각 데이터가 이미지 인코더와 텍스트 인코더로 들어가 처리된다. 이미지 인코더의 결과로 하나의 토큰 배열이 나오고, 텍스트 인코더의 결과로 하나의 토큰 배열이 나오면, 모델은 각 길이 만큼의 행렬(N x N)을 만들어, 각 토큰과의 유사도를 계산한다. 함께 입력된 이미지-텍스트에 대한 유사도는 이 정방행렬의 대각행렬의 주대각원소에 해당한다. 이 부분의 유사도는 1에 가까워지도록, 나머지의 유사도는 0에 가까워지도록 학습을 진행한다.

이후 새로운 분류 데이터를 생성할 때는, 이미지 하나와 이미지를 표현하는 단어를 문장화해서(개 -> 개 사진) 입력한다. 그러면 모델에서 이 이미지에 대해 문장화한 텍스트의 토큰과의 유사도를 계산하고, 가장 유사도가 높은 문장을 선택해서 출력하게되는 것이다.

![CLIP 이미지 인코더]({{ "/assets/images/posts/llava-paper-review/05.png" | relative_url }})
*출처: Medium, Understanding CLIP for vision language models*

나는 그 중 이미지 인코더만 자세히 살펴보았다. 이미지 인코더에서는 이미지를 픽셀 단위로 나눠 납작하게 정렬한다. 모델이 정의해둔 패치 사이즈로 이미지를 분할한 뒤에, 일렬로 나열한다고 생각하면 된다. 이 나열한 이미지 시퀀스를 토큰으로 변환하고, 이미지의 위치 정보를 이 토큰에 더한다. 이미지 시퀀스가 숫자 토큰이 되고, 숫자 토큰끼리 덧셈 계산을 하는 것으로 이해했다.

그 뒤에, 이미지 정보를 요약해서 담을 빈 토큰인 CLS(Special Classification token) 토큰을 맨 앞에 추가한 뒤 트랜스포머를 여러번 거친다. 트랜스포머의 구성에 대해서는 여기서 설명하지 않겠다. CLIP 모델은 여러층의 트랜스포머를 거치고 난 토큰에서, CLS 토큰만 가져와 텍스트 토큰과 유사도를 계산한다. 반면 LLaVA 모델에서는 마지막 트랜스포머를 거치기 직전의 토큰에서도, CLS 토큰을 제외한 나머지 토큰을 가져와 사용한다. 마지막 트랜스포머를 거치면 이미지의 특징들이 압축되어 세밀한 정보를 담을 수 없다고 생각하여 이전 층의 토큰, 거기서도 요약 토큰을 제외하고 사용한다고 한다.

**Vicuna (LLaMA)**

Vicuna는 언어 모델의 기반이 된 Transformer를 파인튜닝한 모델인 LLaMA를, 또 한번 파인튜닝한 모델이다. Meta에서 공개했던 모델인 LLaMA에서 자연스러운 출력을 위해 ChatGPT와의 대화 내용 데이터를 통해 파인튜닝해 대화를 잘 하도록 학습한 것이다.
LLaMA는 Transformer 모델이 적은 파라미터일 때에도 높은 성능을 보일 수 있도록 RMS 정규화, SwishGLU, 상대위치정보를 트랜스포머층에 활용한 모델인데, 자세한 내용은 여기에서 다루지 않겠다.

#### LLaVA 모델 학습 방법

이러한 구조의 LLaVA는 두 단계에 거쳐서 모델을 학습시킨다. 1) 이미지 인코더의 output을 언어 모델의 input으로 변환하는 선형 레이어를 학습하고, 2) 이미지를 넣었을 때 원하는 응답이 나오도록 언어 모델을 학습한다. 1)에 대해 학습할 때에는 이미지 인코더와 언어모델을 freeze한 상태로 선형 투영 레이어만 학습하고, 2)에 대해 학습할 때에는 이미지 인코더만 freeze한 다음, 선형레이어와 언어모델을 학습시킨다. 2)를 학습시키는 과정은 다음과 같다.

![질문-응답 시퀀스]({{ "/assets/images/posts/llava-paper-review/06.png" | relative_url }})

이들은 학습을 위해 각 이미지마다 질문-응답 시퀀스를 만들었다. q는 질문 벡터, a는 우리가 원하는 응답 벡터, T는 한 이미지에 대한 진행 턴 횟수이다. 즉 3번째 질문이면 X_q^3로 표기한다.

![X_instruct 정의]({{ "/assets/images/posts/llava-paper-review/07.png" | relative_url }})

그 다음, 시퀀스를 가지고 학습에 사용할 X_instruct를 정의했다. 1번째 턴에서는 이미지와 1번째 질문을 사용하는데, 이 때 입력 순서를 고정하지 않도록 랜덤하게 이미지와 질문의 순서를 바꿔 입력한다. 이후 2번째 턴에서부터는 턴 수에 맞는 질문을 입력한다.

![학습 입력 형태]({{ "/assets/images/posts/llava-paper-review/08.png" | relative_url }})

실제로 모델을 학습시킬 때는 다음과 같은 형태로 데이터가 들어가게 된다.

시스템 제어 메시지를 먼저 입력한 후, Human이 입력하는 입력값 X_instruct과 모델이 우리에게 반환하기를 바라는 값인 정답 X_a를 순차적으로 입력한다. 이와 같이 Human과 Assistant로 구분지어 입력값을 넣어 모델이 Assistant가 출력해야하는 값을 학습하도록 유도한다.

![응답 확률 수식]({{ "/assets/images/posts/llava-paper-review/09.png" | relative_url }})

모델은 학습 과정으로 통해 Assistant가 출력하길 바라는 정답 응답인 X_a와 자신이 생성한 응답을 비교해 계산해 모델을 개선한다. 이들은 모든 회차 i에 대해 이미지와 지시문을 입력했을 때 정답 응답이 나올 확률을, 이미지와 i번째 이전 지시문과 응답값을 넣었을 때, 이번 i번째 응답이 나올 확률을 구해 곱하는 식으로 정의한다. 즉 (이미지를 알고 있을 때 1번째 정답 응답을 받을 확률) * (이미지와 1번째 지시문과 1번째 정답 응답을 알고 있을 때, 2번째 정답 응답을 받을 확률) * ... 식으로 계산되는 것이다.

이 때 정답 응답을 받을 확률은 각 토큰이 나올 확률을 모두 곱해서 계산한다. 예를 들어, 사과 사진과 함께 "이 사진에 있는게 뭐야?" 라는 지시문에 "이것은 사과입니다."라는 정답 응답이 나올 확률은, 1) "이것은" 이라는 토큰이 나올 확률, 2) 사진-지시문과 "이것은" 이라는 토큰이 있을 때 "사과" 라는 토큰이 나올 확률, 3) 사진- 지시문과 "이것은","사과" 토큰이 있을 때 "입니다" 가 나올 확률, 4) 사진-지시문과 "이것은","사과","입니다" 토큰이 있을 때 &lt;EOF&gt;가 나올 확률을 곱한 것이다. 이런 식으로 응답이 나올 확률을 높이는 방향으로 모델을 학습한다.

#### LLaVA 학습 데이터 생성

이러한 구조의 LLaVA를 학습시키려면 이미지와 지시문 쌍으로 이루어진 데이터들이 필요하다. 이들은 이미지에 대한 지시문 쌍을 만들기 위해 GPT4를 활용했다. 언어모델인 GPT4에게 이미지에 대한 설명을 넣어 질문(지시문)을 생성하도록 요청했다.

![GPT-4로 지시문 데이터 생성]({{ "/assets/images/posts/llava-paper-review/10.png" | relative_url }})

이미지에 있는 사물을 Bounding Box로 표현하여, 각 박스에서 가리키고 있는 대상에 대한 외형을 묘사했다. 그리고 각 bounding box의 위치 정보를 수치로 입력했다. 그 결과 대화, 상세 설명, 복합 추론형의 3가지 유형의 지시문 데이터를 생성할 수 있었다.

Ref.

[1] Visual Instruction Tuning ([https://arxiv.org/pdf/2304.08485](https://arxiv.org/pdf/2304.08485))

[2] Vicuna: An Open-Source Chatbot Impressing GPT-4 with 90%* ChatGPT Quality ([https://lmsys.org/blog/2023-03-30-vicuna/](https://lmsys.org/blog/2023-03-30-vicuna/))

[3] Learning Transferable Visual Models From Natural Language Supervision ([https://arxiv.org/pdf/2103.00020](https://arxiv.org/pdf/2103.00020))

[4] LLaMA: Open and Efficient Foundation Language Models ([https://arxiv.org/pdf/2302.13971](https://arxiv.org/pdf/2302.13971))

[5] CLIP: Connecting text and images ([https://openai.com/index/clip/](https://openai.com/index/clip/))

[6] Understanding CLIP for vision language models ([https://medium.com/self-supervised-learning/understanding-clip-for-vision-language-models-43b700a4aa2b](https://medium.com/self-supervised-learning/understanding-clip-for-vision-language-models-43b700a4aa2b))
