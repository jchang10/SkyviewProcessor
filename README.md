# SkyviewProcessor

# use showdates to show the segments of flight
$ python3 skyview.py sample.csv showdates

# use filter to filter only the wanted segments. wrte to outfile
$ python3 skyview.py sample.csv showdates --outfile out.csv --start "2017-01-28" --end "2017-01-29 00:46:34"

# create the session and csrftoken cookie
$ http --session=test GET https://www.savvyanalysis.com/login

# copy the csrftoken and pass in form csrfmiddlwaretoken value
$ http --form --session=test POST https://www.savvyanalysis.com/login username=jc-savvyanalysis@jline.com password=blahblah csrfmiddlewaretoken=rOCkE61UTyWLcQoVwPRGNCkO9Ygosp7F Referer:https://www.savvyanalysis.com/login

# upload file to airport_id=3434. unfortunately, keep getting WantWriteError due to HTTPS i think. occurred when using
#  debian version of httpie based on python2.7.
# running using virtualenv with httpie based on python3.4.2 seems to work fine
$ http --form --session=test POST https://www.savvyanalysis.com/upload_files/3434 name="test1" aircraft_id="3434" file@out.csv

# EMACS
M-x elpy-enable
M-x elpy-mode

