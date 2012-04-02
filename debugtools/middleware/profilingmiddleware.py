from operator import itemgetter
import sys
import tempfile
import hotshot
import hotshot.stats
from cStringIO import StringIO
from django.conf import settings
from django.db import connection
from django.http import HttpResponse
from django.utils import simplejson
from django.utils.encoding import force_unicode


class ProfilingMiddleware(object):
    """
    Profiling middleware
    """
    allowed_content_types = ("text/html", "application/xhtml+xml", "application/json")


    def is_regular_page(self, request, response):
        return response['Content-Type'].split(';')[0] in self.allowed_content_types

    def is_profile_request(self, request):
        return settings.DEBUG and request.GET.has_key('prof')


    def process_request(self, request):
        if self.is_profile_request(request):
            #self.tmpfile = tempfile.NamedTemporaryFile()  need .name property
            request._prof_file = '/Users/maru/dev/curquma/profile.prof'
            request._prof = hotshot.Profile(request._prof_file)


    def process_view(self, request, callback, callback_args, callback_kwargs):
        if self.is_profile_request(request):
            return request._prof.runcall(callback, request, *callback_args, **callback_kwargs)


    def process_response(self, request, response):
        if settings.DEBUG and self.is_regular_page(request, response):
            stats_str = ''
            if self.is_profile_request(request):
                request._prof.close()

                out = StringIO()
                old_stdout = sys.stdout
                sys.stdout = out

                stats = hotshot.stats.load(request._prof_file)
                #stats.strip_dirs()
                stats.sort_stats('time', 'calls')
                stats.print_stats()

                sys.stdout = old_stdout
                stats_str = out.getvalue()

            queries = sorted(connection.queries, key=itemgetter('time'), reverse=True)

            if response:
                debug = {
                    'stats': stats_str,
                    'query_count': len(queries),
                    'query_time': sum(float(q['time']) for q in queries),
                    'queries': queries,
                }
                if 'json' in response['Content-Type']:
                    response.content = response.content[:-1] + ', "DEBUG": {0}}}'.format(simplejson.dumps(debug))
                else:
                    querymsg = "Profiling:\n{stats}\n\nTotal {query_count} queries taking {query_time}sec:\n\n{queries_text}\n".format(
                        queries_text='\n\n'.join(q['time'] + 'sec: ' + _format_query(q['sql']) for q in queries),
                        **debug
                    )

                    if response.status_code == 302 and not request.is_ajax():
                        # Also display POST redirects in Firefox
                        newurl = response['Location']
                        response = HttpResponse(querymsg, content_type='text/plain')
                        response['Refresh'] = '0; url={0}'.format(newurl)
                    else:
                        pre = u"<pre>{0}</pre>".format(_escape_tags(querymsg))
                        html = response.content.split('</body>')
                        if len(html) > 1:
                            response.content = u"{0}{1}</body>{2}".format(html[0], pre, html[1])
                        else:
                            response.content += pre

        return response


def _format_query(sql):
    return sql.replace(' WHERE ', '\n WHERE ') \
        .replace(' FROM ', '\n FROM ')\
        .replace(' INNER JOIN ', '\n INNER JOIN ') \
        .replace(' LEFT OUTER JOIN ', '\n LEFT OUTER JOIN ') \
        .replace(' OUTER JOIN ', '\n OUTER JOIN ')

def _escape_tags(html):
    # Only escape mandatory tags, to keep debugging output for Ajax requests clean
    return force_unicode(html).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

