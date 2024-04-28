# google-drive-monitor
Monitor Google Drive new files and make sure they are private.

# Initial setup
Go through the quickstart guide and make sure you complete all the Set Up [Python Quickstart guide](https://developers.google.com/drive/v3/web/quickstart/python)).

# Requirements and Dependencies 
pip install the next packages:
```
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib python-dateutil
```

# Necessary Permissions Scopes and Tokens
1. Permissions required as described in the Python Quickstart guide
   make sure you have access to the account you are going to use.
2. Scopes for which we request an access token are written in the global variable SCOPES inside
3. Tokens: The code generates an Access Token with the scopes described above and keeps it in the file ```token.json```

# Usage
1. Download the repo to a working directory
2. In the same directory add your ```credentials.json``` file from the Drive API
3. From the same working directory execute:
   ```python main.py```
4. In the first execution or after a while not using the code, your browser will open and you'll have to enter valid credentials as provided to the testing account in the Google Drive API
5. A new file will be created ```token.json``` which will contain your access token to the requested scopes
6. If you want, you should use a ```crontab``` (Linux) or ```service``` (Windows) for a scheduled execution of this code.*

# more info about usage
* The code makes use of two other files:
* ```files_changed_by_program.json``` - Which keeps the Ids of the files that the program changed their permissions.
* ```last_check_time.txt``` - Which keeps the last execution time to know which files are new.
* We treat files in the Trash same as normal files. This can be changed if needed (ToDo)

# Examples
* an example of a drive with 3 files which one of them is public
![image](https://github.com/YanirLA/google-drive-monitor/assets/61561152/e6de9d4a-9a6c-4d3b-ad3b-0d39baf27bb6)
* The code ouput will be:
  ![image](https://github.com/YanirLA/google-drive-monitor/assets/61561152/e514f1e9-5c5a-4508-832b-8c1b89247ecb)

* The publicly access file will chnage to private:
  ![image](https://github.com/YanirLA/google-drive-monitor/assets/61561152/6b8d1ef3-21fd-4ed0-a760-fb7e452105dd)

* If we run the code again the output will be:
  ![image](https://github.com/YanirLA/google-drive-monitor/assets/61561152/32e1e7fe-ecd2-44ed-a4ad-6c3563a97824)




# Known Issues
* *A schedule execution will still require once in a while to reauth your account manually every time the access token is not valid anymore.
* for any unknown exception try to delete the ```token.json``` and run again
* After a file is being changed to private, its considered as a new file for the next run because the modification time is greater then last check time. But nothing will happen in the next run because its already private.


# Attack surfaces general ideas
ideas the not tested or checked, just general ideas.
* drives.hide - lets you hide a drive from the default view, maybe we can copy private files to this drive with different permissions for the files while stay unnoticible
*  file revisions - maybe there is a way to hide malicious content in a file revision
*  replies / comments - maybe there is an XSS exploit in the content field (it uses html to show the content)

# ToDo's
* add an option to ignore files in the Trash
* more precise Exceptions handling 
