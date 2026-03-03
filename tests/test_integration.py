#!/usr/bin/env python3
"""Test post-processing integration"""

from writer import write_post

sample_data = {
    'keyword': '테스트',
    'article_title': '테스트 뉴스',
    'article_body': '이것은 테스트 기사입니다. 테스트 기사는 테스트 목적으로 작성되었습니다. 테스트 기사는 테스트 시스템을 검증하기 위해 사용됩니다. 테스트를 통해 시스템이 제대로 작동하는지 확인할 수 있습니다.',
    'topic': '기타',
    'news_url': 'https://example.com/test'
}

print('\n[테스트] post-processing 통합 검증 중...\n')

result = write_post(sample_data)

if result:
    title = result['title']
    body = result['body']
    score = result.get('seo_score', 0)

    print('[성공] 포스트 생성됨')
    print(f'  제목: ({len(title)}자) {title}')
    print(f'  본문: ({len(body)}자)')
    print(f'  SEO점수: {score}점')
    print()
    print('  [검증]')
    print(f'    제목 범위 30-45: {"OK" if 30 <= len(title) <= 45 else "FAIL"}')
    print(f'    본문 범위 350-450: {"OK" if 350 <= len(body) <= 450 else "FAIL"}')
    print(f'    SEO점수 80점 이상: {"OK" if score >= 80 else "FAIL"}')
else:
    print('[실패] 포스트 생성 실패')
