import sys
import os
import json
import datetime
from influxdb import InfluxDBClient

# CONFIG HERE
INFLUXDB_HOST = "localhost"
INFLUXDB_PORT = 8086
INFLUXDB_DB = "harbor"
MEASUREMENT_NAME = "hub.example.com"
# DON'T EDIT BELOW

registry_path = sys.argv[1]

def write_to_influx(project_with_size_dict):
    client = InfluxDBClient(host=INFLUXDB_HOST, port=INFLUXDB_PORT,database=INFLUXDB_DB)
    for project_name,size in project_with_size_dict.items():
        json_body = [
            {
                "measurement": MEASUREMENT_NAME,
                "tags": {
                    "project": project_name,
                },
                "time": str(datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")),
                "fields": {
                    "size": size,
                }
            }
        ]
        client.write_points(json_body)

def walk_through_repo(path):

    image_with_size_list = []
    project_with_size_dict = {}

    repositories_path = path + "/repositories/"
    for (dirpath, dirnames, filenames) in os.walk(repositories_path):
        for dirname in dirnames:
            if "current" in dirname:
                
                image_with_tag = dirpath.replace(repositories_path,"").replace('/_manifests/tags/',":")

                image_manifest_file = dirpath + "/" + dirname + "/link"
                with open(image_manifest_file,"r") as f:
                   manifest_hash = f.readline().split(":")[1]

                manifest_json_path = path + "/blobs/sha256/" + manifest_hash[0:2] + "/" + manifest_hash + "/data"
                
                image_size_byte = 0
                try:
                    with open(manifest_json_path,"r") as f:
                        manifest_json = json.load(f)
                    try:
                        for layer in manifest_json['layers']:
                            image_size_byte += int(layer['size']) 
                    except:
                        pass
                except:
                    pass

                each_image_with_size = {}
                each_image_with_size['image_with_tag'] = image_with_tag
                each_image_with_size['image_size_byte'] = image_size_byte

                image_with_size_list.append(each_image_with_size)

                project_name = image_with_tag.split('/',1)[0]
                if project_name in project_with_size_dict:
                    project_with_size_dict[project_name] += image_size_byte
                else:
                    project_with_size_dict[project_name] = image_size_byte
                

    return project_with_size_dict


if __name__ == '__main__':
    print("Registry Path is: " + registry_path)
    project_with_size_dict = walk_through_repo(registry_path)
    write_to_influx(project_with_size_dict)