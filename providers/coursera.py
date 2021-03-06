from provider import ProviderBase
import requests
from datetime import date


class Coursera(ProviderBase):
    def __init__(self):
        self.course_data = []

    def get_courses(self):
        coursera_url = "https://www.coursera.org/maestro/api/topic/list?full=1"

        response = requests.get(coursera_url)
        courses = response.json()
        catalog = []
        for item in courses:
            course = Coursera.get_schema_map()
            print "Processing Course: Coursera - {}".format(item.get("name", "Unknown").encode('utf-8'))
            try:
                #get required items
                course['course_name'] = item['name']
                course['providers_id'] = item["short_name"]
                course['provider'] = "coursera"
                course['language'] = Coursera.get_valid_language(item['language'])
                course['instructor'] = item['instructor']
                course['course_url'] = "http://class.coursera.org/{}/".format(item["short_name"])
                #lets create an ID for the record
                course['id'] = Coursera.create_id(course['provider'] + course["course_name"])
                #get institution data
                university = item['universities'][0]
                institution = {
                    "name": university['name'],
                    "description": university.get("description", None),
                    "id": Coursera.create_id(university['name']),
                    "website": university["home_link"],
                    "logo_url": university["logo"],
                    "city": university["location_city"],
                    "state": university["location_state"],
                    "country": university["location_country"]
                }
                course['institution'] = institution

                #get the data we need from the full course detail
                more_details = self.__get_course_detail(course["providers_id"])

                course['full_description'] = more_details.get("about_the_course", "not found")
            except KeyError:
                #we don't have all required fields, skip for now
                #log it
                continue

            #get MEDIA INFO
            media = {
                "photo_url": more_details.get("photo", None),
                "icon_url": more_details.get("large_icon", None),
                "video_url": more_details.get("video_baseurl", None),
                "video_type": "mp4",
                "video_id": more_details.get("video_id", None)
            }

            course["media"] = media

            #get optional fields
            course['short_description'] = item.get('short_description', None)
            course['categories'] = item.get('categories', [])
            course['workload'] = more_details.get('estimated_class_workload', None)
            catalog.append(item['short_name'])

            #get tags
            tags = []
            for cat in more_details["categories"]:
                tags.append(cat["name"])

            course["tags"] = tags

            #get the session data
            for c in item.get('courses'):
                session = {}
                session['duration'] = c.get('duration_string', None)
                session['provider_session_id'] = c.get('id', None)
                #get Start Date
                if all(name in c for name in ['start_year', 'start_month', 'start_day']):
                    try:
                        session['start_date'] = date(c['start_year'], c['start_month'], c['start_day']).strftime('%Y%m%d')
                    except TypeError:
                        #we don't have a valid start date, skip it
                        continue
                else:
                    #missing a start date, skip it
                    continue
                course['sessions'].append(session)
            self.course_data.append(course)

        return self.course_data

    def __get_course_detail(self, id):
        response = requests.get("https://www.coursera.org/maestro/api/topic/information?topic-id=" + id)
        return response.json()
