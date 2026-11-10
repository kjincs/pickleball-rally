import sys
import unittest
import json
import shutil
import tempfile
from datetime import date, datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1] / 'scripts'))
import generate as g

class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.editions = {'edition-1':{'stories':[{'id':'story-1','title':'Women building clubs','category':'Community'}]}}
    def issue(self,number=1,author='friend',score='5 — Excellent',updated='2026-11-09T10:00:00Z',story='story-1'):
        return {'number':number,'title':'[Review] edition-1 / story-1','user':{'login':author},'updated_at':updated,
                'body':f'### Edition ID\n\nedition-1\n\n### Story ID\n\n{story}\n\n### Score\n\n{score}\n\n### What should we change?\n\nMore like this\n\n### Your thoughts\n\nMore local clubs, please.'}
    def test_edited_or_duplicate_review_counts_once(self):
        old=self.issue();new=self.issue(2,score='2 — A little useful',updated='2026-11-09T12:00:00Z')
        reviews=g.parse_reviews([new,old],['Friend'],self.editions)
        self.assertEqual(len(reviews),1)
        self.assertEqual(reviews[0]['score'],2)
    def test_unknown_author_and_story_are_not_feedback_in_trusted_mode(self):
        issues=[self.issue(author='stranger'),self.issue(story='missing')]
        self.assertEqual(g.parse_reviews(issues,['friend'],self.editions),[])
    def test_whole_edition_review_and_empty_comment(self):
        issue=self.issue(story='edition');issue['body']=issue['body'].replace('More local clubs, please.','_No response_')
        reviews=g.parse_reviews([issue],['friend'],self.editions)
        self.assertEqual(reviews[0]['title'],'Whole edition')
        self.assertEqual(reviews[0]['comment'],'')
    def test_canonicalization_prevents_tracking_link_duplicates(self):
        self.assertEqual(g.canonical_url('https://example.com/story/?utm_source=mail#top'),'https://example.com/story')
        with self.assertRaises(ValueError): g.canonical_url('javascript:alert(1)')
    def test_uncited_stale_future_and_repeated_news_are_rejected(self):
        base={'title_zh':'标题','summary_zh':'摘要','why_zh':'理由','source_language':'en','source_type':'reporting','title':'A useful story','summary':'An original summary.','why':'It helps readers.','category':'News','source':'Source','kind':'news','published_at':'2026-11-08','url':'https://example.com/good'}
        candidates=[base,{**base,'url':'https://example.com/invented'},
                    {**base,'url':'https://example.com/stale','published_at':'2025-01-01'},
                    {**base,'url':'https://example.com/future','published_at':'2026-11-12'},
                    {**base,'url':'https://example.com/old?utm_source=mail'}]
        cited={'https://example.com/'+p for p in ['good','stale','future','old']}
        result=g.checked_stories(candidates,cited,{'https://example.com/old'},date(2026,11,9),30)
        self.assertEqual([s['url'] for s in result],['https://example.com/good'])
    def test_news_requires_date_but_background_read_may_be_undated(self):
        base={'title_zh':'标题','summary_zh':'摘要','why_zh':'理由','source_language':'en','source_type':'reporting','title':'Useful background','summary':'Context.','why':'Useful.','category':'Community','source':'Source','published_at':None,'url':'https://example.com/context'}
        self.assertEqual(g.checked_stories([{**base,'kind':'news'}],{base['url']},set(),date(2026,11,9),30),[])
        self.assertEqual(len(g.checked_stories([{**base,'kind':'evergreen'}],{base['url']},set(),date(2026,11,9),30)),1)
    def test_comments_only_from_any_github_user_in_open_pilot(self):
        issue=self.issue(author='new-friend',score='Select a score / 请选择评分')
        issue['body']=issue['body'].replace('More like this','Select a preference / 请选择')
        reviews=g.parse_reviews([issue],None,self.editions)
        self.assertEqual(len(reviews),1)
        self.assertIsNone(reviews[0]['score'])
        self.assertIsNone(reviews[0]['direction'])
        self.assertEqual(reviews[0]['comment'],'More local clubs, please.')
    def test_empty_placeholder_review_is_not_counted(self):
        issue=self.issue(score='Select a score')
        issue['body']=issue['body'].replace('More like this','Select a preference').replace('More local clubs, please.','_No response_')
        self.assertEqual(g.parse_reviews([issue],None,self.editions),[])
    def draft(self):
        config=g.load('config.json')
        today=str(datetime.now(ZoneInfo(config['timezone'])).date())
        story={'title':'New story','title_zh':'新的故事','summary':'A source-grounded summary.',
               'summary_zh':'有来源的摘要。','why':'Useful context.','why_zh':'实用背景。',
               'category':'Community','source':'Author','source_language':'zh','source_type':'reporting',
               'kind':'evergreen','published_at':None,'url':'https://example.com/new-story'}
        return {'date':today,'feedback_note':'No feedback yet.','feedback_note_zh':'暂无评论。','guidance':[],
                'review_count':0,'stories':[story],
                'sources':[{'url':story['url'],'checked_at':today,'notes':'Read the full original source.'}]}
    def test_codex_draft_publishes_without_api_key_and_preserves_archive(self):
        config=g.load('config.json');draft=self.draft();old_index=g.load('data/index.json')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);shutil.copytree(g.ROOT/'data',root/'data');shutil.copy2(g.ROOT/'config.json',root/'config.json')
            with patch.object(g,'ROOT',root),patch.dict(g.os.environ,{},clear=True):
                g.publish_draft(draft,config)
                index=g.load('data/index.json')
                self.assertEqual(index['editions'][1:],old_index['editions'])
                edition=g.load('data/editions/'+index['editions'][0]+'.json')
                self.assertEqual(edition['research_method'],'codex')
                g.validate_site()
    def test_bad_draft_cannot_modify_publication(self):
        draft=self.draft();draft['sources'][0]['url']='https://example.com/unrelated'
        with patch.object(g,'write') as write:
            with self.assertRaises(ValueError):g.publish_draft(draft,g.load('config.json'))
            write.assert_not_called()
    def test_republishing_same_story_is_rejected(self):
        draft=self.draft();config=g.load('config.json');existing=g.load('data/editions/'+g.load('data/index.json')['editions'][0]+'.json')['stories'][0]['url']
        draft['stories'][0]['url']=existing;draft['sources'][0]['url']=existing
        with patch.object(g,'write') as write:
            with self.assertRaises(ValueError):g.publish_draft(draft,config)
            write.assert_not_called()
    def test_social_homepage_is_not_a_story(self):
        s={'url':'https://example.com/','category':'Community','kind':'evergreen','source_type':'social','source_language':'en'}
        self.assertEqual(g.checked_stories([s],{s['url']},set(),date(2026,11,9),30),[])
    def test_repository_content_validates(self):
        g.validate_site()

if __name__ == '__main__': unittest.main()
