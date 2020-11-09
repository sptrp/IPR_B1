""" 
B1 websocket server
"""

# TODO: 
# pip install asyncio
# pip install websockets
# pip install pandas
# pip install lxml

import asyncio
import websockets
import logging
import pandas as pd  
import csv
import lxml.etree as et
import sys
import os
import helper 

# logger
logging.basicConfig(level=logging.DEBUG)

xml = os.path.join(sys.path[0], 'kurse.xml')
xml_snip = os.path.join(sys.path[0], 'kurse_snippet.xml')     #Quelle: https://stackoverflow.com/questions/4060221/how-to-reliably-open-a-file-in-the-same-directory-as-a-python-script
schema = os.path.join(sys.path[0], 'kurse.xsd')         #Damit es unter Linux, Windows und Mac laeuft
request_schema = os.path.join(sys.path[0], 'request.xsd')  


# parse kurse and return xml or csv
def find_all_courses(format):
  tree = et.parse(xml)
  root = tree.getroot()
  chunk = []

  if (format == 'xml'):
    output_string = et.tostring(root, encoding='utf8', method='xml')

    # Split message on 15 chunks, because it's too big (Nikolai's advice)
    chunk.append(output_string[0 : 123460])
    chunk.append(output_string[123460 : 246920])
    chunk.append(output_string[246920 : 493840])
    chunk.append(output_string[493840 : 987680])
    chunk.append(output_string[987680 : 1975360])
    chunk.append(output_string[1975360 : 2963040])
    chunk.append(output_string[2963040 : 3950720])
    chunk.append(output_string[3950720 : 4938400])
    chunk.append(output_string[4938400 : 5926080])
    chunk.append(output_string[5926080 : 6913760])
    chunk.append(output_string[5926080 : 6913760])
    chunk.append(output_string[6913760 : 7913760])
    chunk.append(output_string[7913760 : 8913760])
    chunk.append(output_string[8913760 : 9913760])
    chunk.append(output_string[9913760 : 10913760])
    chunk.append(output_string[10913760 : 11913760])
    chunk.append(output_string[11913760 : -1])

<<<<<<< HEAD
    #print
=======
>>>>>>> master
    return chunk

  else: 
    rows = []
    spamreader = ''
    cols = ['Guid', 'Nummer', 'Name', 'Untertitel']
    # give the temp data distinct name
    file_name = 'courses.%s.csv' % os.getpid()

    try:
      with open(file_name, 'w', newline='', encoding="utf8") as file:
        # parse elements and write to csv
        for elem in root:

          rows.append({ "Guid": elem.find('guid').text, "Nummer": elem.find('nummer').text, 
                        "Name": elem.find('name').text, "Untertitel": elem.find('untertitel').text 
                      })
        dataframe = pd.DataFrame(rows, columns = cols) 
        dataframe.to_csv(file_name)
    except IOError:
      print("I/O error")
    finally:
      with open(file_name, encoding="utf8") as f:
        # place csv data in output string
        output_string = f.read() + '\n'
      # remove temp datei
      os.remove(file_name)
    
    return output_string 


def find_elems_from_query(format, path, calltype):
  joined_string = ""
  # check format
  if (format == 'xml'):
    tree = et.parse(xml)
    root = tree.getroot()
    elems = root.xpath(path)

    if (calltype == 'mcs' or calltype == 'div'):
      for targ in elems: 
        for dept in targ.xpath('ancestor-or-self::veranstaltung'):
          joined_string = joined_string + et.tostring(dept, encoding="unicode", pretty_print=True)
        
    else:
      # https://stackoverflow.com/questions/21746525/get-all-parents-of-xml-node-using-python
      joined_string = joined_string.join([et.tostring(elem, encoding="unicode", pretty_print=True) for elem in elems])

    return joined_string
    
  else:   
    my_dict = {}
    rows = []
    tree = et.parse(xml)
    root = tree.getroot()
    cols = [' Name', ' Untertitel', ' Minimale Teilnehmerzahl', ' Maximale Teilnehmerzahl', ' Beginn Datum']
    # give the temp data distinct name
    file_name = 'my_courses%s.csv' % os.getpid()

    # parse all found elements and make dict
    for targ in root.xpath(path): # https://stackoverflow.com/questions/21746525/get-all-parents-of-xml-node-using-python
      for dept in targ.xpath('ancestor-or-self::veranstaltung'):
        my_dict[dept[0].text] = { "Name" : dept[2].text, "Untertitel" : dept[3].text,
                                  "Minimale Teilnehmerzahl" : dept[5].text,
                                  "Maximale Teilnehmerzahl" : dept[6].text,
                                  "Beginn Datum" : dept[8].text
                                }                                                                   
    try:
      with open(file_name, 'w') as file:
        for elem in my_dict:
          # parse elements and write to csv
          rows.append({ " Name": my_dict[elem]['Name'], " Untertitel": my_dict[elem]['Untertitel'],
                        " Minimale Teilnehmerzahl": my_dict[elem]['Minimale Teilnehmerzahl'], 
                        " Maximale Teilnehmerzahl": my_dict[elem]['Maximale Teilnehmerzahl'], 
                        " Beginn Datum": my_dict[elem]['Beginn Datum'] 
                      })
        dataframe = pd.DataFrame(rows, columns = cols) 
        dataframe.to_csv(file_name)
    except IOError:
        print("I/O error")
    finally:
      with open(file_name, encoding="utf8") as f:
        # place csv data in output string
        output_string = f.read() + '\n'
      # remove temp file
      os.remove(file_name)

    return output_string

# validator for incoming xml  
def xml_validator(input, schema):
  with open(input, 'rb') as x:
    # create parser from xsd schema
    with open(schema, 'rb') as s:
      xml_root = et.tostring(et.XML(x.read()), encoding='utf8', method='xml')
      schema_root = et.XML(s.read())
      val_schema = et.XMLSchema(schema_root)
      parser = et.XMLParser(schema=val_schema)

    try:
      et.fromstring(xml_root, parser) 
      return True # return true if file is valid
    except et.XMLSyntaxError: 
      print("Request Fehler: Falscher Request") # return exception and error message if not

# server
async def echo(websocket, path):
  async for message in websocket:
    
    # validate request
    if xml_validator(xml_snip, schema):

      tree = et.ElementTree(et.fromstring(message))
      # parse format and calltype from request
      format = tree.xpath('//format')[0].text
      calltype = tree.xpath('//calltype')[0].text

      if (calltype == 'acs'):
        if (format == 'xml'):
          response = find_all_courses(format)

          for elem in response:
            await websocket.send(elem)
        else: 
          await websocket.send(str(find_all_courses(format)))

      elif (calltype == 'sse'):
        elem = tree.xpath('//element')[0].text
        value = tree.xpath('//value')[0].text
        # build path
        if (elem == 'divers'):
          calltype = 'div'
          path = helper.path_constructor_divers(value)
          print (path)
        else: 
          path = helper.path_constructor_elem(elem, value) 

        await websocket.send(find_elems_from_query(format, path, calltype))

      elif (calltype == 'mcs'):
        # parse client id from request
        client_id = tree.xpath('//client')[0].text
        # build path
        path = helper.path_constructor_book('kunde', client_id)
        await websocket.send(find_elems_from_query(format, path, calltype) )

    else:
        await websocket.send('Falscher Request')

asyncio.get_event_loop().run_until_complete( websockets.serve(echo, "localhost", 8765, max_size = None) )
print("Running service at https//:localhost:8765")
asyncio.get_event_loop().run_forever()