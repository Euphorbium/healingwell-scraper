# -*- coding: utf-8 -*-
import unicodecsv
from lxml import html, etree
from retrying import retry
from StringIO import StringIO
import re


@retry(wait_random_min=5000, wait_random_max=10000)
def scrape_thread(thread):
    print base+"/community/pr.aspx"+thread.attrib["href"][23:]
    title = thread.text
    qid = re.findall('\d*$', thread.attrib['href'])[0]
    t = html.parse(base+"/community/pr.aspx"+thread.attrib["href"][23:])
    for br in t.xpath("*//br"):
        br.tail = "\n" + br.tail if br.tail else "\n"
    no_signatures = re.sub('<hr.*?/td>', "", etree.tostring(t), flags=re.DOTALL)
    meta = t.xpath('//td[@class="printHead"]')
    posters = set()
    post_content = html.parse(StringIO(no_signatures)).xpath('//td[@class="printBody"]')[1:]
    for i, post in enumerate(zip(meta, post_content)):
        inferred_replies = set()
        local_id = i - 1
        reply_to = qid + "_top" if local_id >= 0 else " "
        poster = post[0].xpath('b')[0].text
        date = post[0].xpath('b')[0].tail[3:]
        content = post[1].text_content()
        unique_id = qid + "_top" if local_id < 0 else qid + "_" + str(local_id)
        for p in posters:
            if p in content:
                inferred_replies.add(p)
        row = [unique_id, qid, local_id, title, poster, date, reply_to, content, ' | '.join(inferred_replies), subforum]
        w.writerow(row)
        f.flush()
        posters.add(poster)

@retry(wait_random_min=5000, wait_random_max=10000)
def parse_page(url):
    for thread in html.parse(url).xpath('//td[@class="msgTopic TopicTitle"]/a'):
        scrape_thread(thread)

base = "http://www.healingwell.com"
start = html.parse("http://www.healingwell.com/community/default.aspx")
f = open('healingwell.csv', 'w')
w = unicodecsv.writer(f, encoding='utf-8', lineterminator='\n')
w.writerow(['uniqueID', 'qid', 'localID', 'title', 'poster', 'date', 'replyTo', 'content', 'infered_replies', 'subforum'],)
for forum in start.xpath('//td[contains(@class, "msgTopic ForumName")]/a'):
    subforum = forum.text
    forum_page = html.parse(base+forum.attrib['href'])
    pages = forum_page.xpath('//br[following-sibling::text()="Forum Page Listing :  "]/../a')

    for thread in forum_page.xpath('//td[@class="msgTopicAnnounce TopicTitle"]/a'):
        scrape_thread(thread)

    if pages:
        for page in xrange(1, int(pages[-1].text)+2):
            print "New forum page", base + forum.attrib['href']+str(page)
            parse_page(base+forum.attrib['href']+"&p"+str(page))

    else:
        parse_page(base+forum.attrib['href'])
