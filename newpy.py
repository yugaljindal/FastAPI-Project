# import sys,os,re,json
# # sys.path.append(os.getcwd())
# from azure_form_recognizer.form_recognizer import analyze_page_data
# from ocr.db_functions import sqlData
# from uuid import uuid1
# from ocr.provision_functions import convertingPDFtoImagejpeg
# from ocr.utility_functions import remove_folder_files
# from ocr.image_functions import align_images
# from azure_storage_account.file_operations import azure_storage_account
# import fitz
# import requests
# from starlette.config import Config
# from app.config.settings import CF_SCAN_SUPPORTED_FORMS


# config = Config('.env')

# class Doc_scanner:
#     def __init__(self,file_path) -> None:
#         self.file_path = file_path
    

#     def convert_pdf_to_jpeg(self,pathToPDF,output_dir=""):
#         pdf_page_path_list = list()
#         if output_dir == "":
#             path = str(uuid1())
#         else:
#             path = output_dir
        
#         storage_obj = azure_storage_account()
#         file_data = storage_obj.read_file(file_path=pathToPDF) 
#         dpi = 360  # choose desired dpi here
#         zoom = dpi/ 72  # zoom factor, standard: 72 dpi
#         magnify = fitz.Matrix(zoom, zoom)  # magnifies in x, resp. y direction
#         doc = fitz.open("pdf",file_data)  # open document
#         text = ""

#         for page in doc:
#             text = page.get_text("text")
#             pix = page.get_pixmap(matrix=magnify)  # render page to an image
#             output_image_bytes = pix.pil_tobytes(format="JPEG",optimize=True)
#             pdf_page_path = path + os.sep +'page'+ str(page.number + 1) +'.jpg'
#             print(pdf_page_path)
#             if text != "":
#                 isVersion = re.search("ACORD\s[0-9]{1,}\s[A-Z\s]{0,3}\(.*\)",text)
#                 if isVersion:
#                     acord_form_version = isVersion.group()
#                     acord_form_version = acord_form_version.replace(" ","")
#                     isPageNumber = re.search("Page\s[1-9]{1,}\sof\s[1-9]{1,}",text)
#                     if isPageNumber:
#                         page_number = isPageNumber.group()
#                         page_number = int(page_number[5])
#                     else:
#                         page_number = 1

#                     pdf_page_path_list.append((pdf_page_path,(acord_form_version,page_number)))
                
#                 else:
#                     pdf_page_path_list.append((pdf_page_path,False))
                    
#             else:
#                 pdf_page_path_list.append((pdf_page_path,False))

#             storage_obj.create_file(file_path=pdf_page_path,data=output_image_bytes)

#         return path, pdf_page_path_list


#     def create_temporary_img_folder(self,folder_perfix=""):
#         try:
#             if folder_perfix == "":
#                 temporary_folder = "tmp/" + str(uuid1())
#             else:
#                 temporary_folder = "tmp/" + str(folder_perfix)
#             #convertingPDFtoImagejpeg(pathToPDF=self.file_path,output_dir=temporary_folder)
#             img_folder_path , image_list = self.convert_pdf_to_jpeg(pathToPDF=self.file_path,output_dir=temporary_folder)
            
#             return temporary_folder, image_list
        
#         except Exception as e:
#             return None, None
    

#     def scan(self):
#         scan_output = dict()
#         scan_output["status"] = True
#         scan_output["valid_pages"] = 0
#         scan_output["elabels"] = dict()
#         folder_path, image_file_list = self.create_temporary_img_folder()
#         storage_obj = azure_storage_account()
#         if folder_path != None:
#             files_list = storage_obj.get_files_list(perfix=folder_path)
#             files_list.sort()
#             for file in  files_list:
#                 if '.jpg' in file:
#                     print(file)
#                     file_name = file.rsplit('/', 1)[-1]
#                     page_search = re.search("^page.*.jpg$",file_name)
#                     if page_search:
#                         pdf_page_number = page_search.group()
#                         try:
#                             pdf_page_number = int(pdf_page_number[4:-4])
#                         except:
#                             pdf_page_number = ""

#                     if pdf_page_number != "":
#                         scan_output["elabels"][pdf_page_number] = dict()
#                         page_meta_data = self.get_acord_form_version_and_page_number(file)
#                         acord_form_elabels = self.get_acord_form_elabels(acord_form_version = page_meta_data['version'] , page_number = page_meta_data['page_number'])
#                         if len(acord_form_elabels):
#                             align_status = self.align_pdf_image_with_reference_image(pdf_image_path=file,acord_form_version=page_meta_data['version'],acord_form_page_number=page_meta_data['page_number'])
#                             if not align_status:
#                                 continue
#                             try:
#                                 page_data = self.analyze_page(file) # if failed from form regonizer side, try one more time
#                             except:
#                                 page_data = self.analyze_page(file)

#                             elabels_data = self.extract_elabels_data(elabels=acord_form_elabels,page_data=page_data)
#                             scan_output["valid_pages"] +=1
#                             scan_output["elabels"][pdf_page_number]["form_version"] = page_meta_data['version']
#                             scan_output["elabels"][pdf_page_number]["form_page_number"] = page_meta_data['page_number']
#                             scan_output["elabels"][pdf_page_number] = {**scan_output["elabels"][pdf_page_number], **elabels_data}

#             storage_obj.delete_folder(folder_path)
#         return scan_output


#     def pdf_to_page(self,pdf_id=""):
#         """
#         Return pdf pages images path list after converting pdf to images
#         """
#         image_file_list = list()
#         folder_path, image_file_list = self.create_temporary_img_folder(folder_perfix=pdf_id)
#         #if folder_path != None:
#             #storage_obj = azure_storage_account()
#             #file_list = storage_obj.get_files_list(perfix=folder_path)
#             #file_list.sort()
        
#         return image_file_list
    
    


#     def page_scan(self,page_path,form_version="",omit_blank_values=False,endpoint_name=""):
#         """
#         Take page image of acord form and return elabels 
#         """
#         print("the code inside page_scan")
#         page_scan_output = dict()
#         page_scan_output["form_version"]=""
#         page_scan_output["form_page_number"]=""
#         page_scan_output["data"] = dict()
#         page_meta_data = dict()
#         need_alignment = False
#         check_aligned_from_contabo = False
#         try:
#             acord_form_version, acord_form_page_number, page_aligned_status = self.detect_acord_form(page_path)
#             page_meta_data['version'] = acord_form_version
#             page_meta_data['page_number'] = acord_form_page_number
#             if page_aligned_status == False:
#                 need_alignment = True
#             check_aligned_from_contabo = True
#             print("need alignment", need_alignment)
            
#         except:
#             try:
#                 page_data = self.analyze_page(page_path) #if failed from form regonizer side, try one more time
#             except:
#                 page_data = self.analyze_page(page_path)
                
#             print("inside except statement")
        
#             page_aligned_status, page_meta_data = self.check_page_is_aligned(page_data)

#             if page_aligned_status == False:
#                 need_alignment = True

#             if form_version == "" or form_version == False: # True if page is not textable
#                 #page_meta_data = self.get_acord_form_version_and_page_number(page_path)
#                 #need_alignment = True
#                 pass
#             else:
#                 page_meta_data['version'] = form_version[0]
#                 page_meta_data['page_number'] = form_version[1]
                
        

#         scan_flag = True
#         if endpoint_name == "cf-scan" and str(page_meta_data['version']).strip().upper() not in CF_SCAN_SUPPORTED_FORMS:
#             scan_flag = False
        
#         if scan_flag == True:
#             acord_form_elabels = self.get_acord_form_elabels(acord_form_version = page_meta_data['version'] , page_number = page_meta_data['page_number'])
#             if len(acord_form_elabels):
#                 align_status = False
#                 if need_alignment:
#                     align_status = self.align_pdf_image_with_reference_image(pdf_image_path=page_path,acord_form_version=page_meta_data['version'],acord_form_page_number=page_meta_data['page_number'])
                
#                 print("check_aligned_from_contabo",check_aligned_from_contabo)
#                 if align_status or align_status == False:  # make dependent to align_pdf_image_with_reference_image function
#                     if check_aligned_from_contabo: #when aligned checked by contabo and page are aligned then we have to analyze the page
#                         page_data = self.analyze_page(page_path)
                    
#                     elif need_alignment:
#                         print("Inside elif statement")
#                         try:
#                             page_data = self.analyze_page(page_path) #if failed from form regonizer side, try one more time
#                         except:
#                             page_data = self.analyze_page(page_path)
                                                          
#                     elabels_data = self.extract_elabels_data(elabels=acord_form_elabels,page_data=page_data)
#                     if omit_blank_values == True:
#                         elabels_data = dict([(vkey, vdata) for vkey, vdata in elabels_data.items() if(str(vdata).strip())])
                    
#                     page_scan_output["form_version"] = page_meta_data['version']
#                     page_scan_output["form_page_number"] = page_meta_data['page_number']
#                     page_scan_output["data"] = elabels_data

#         return page_scan_output
        
    
#     def check_page_is_aligned(self,page_data):
#         page_aligned_status = False
#         page_meta_data = dict()
#         page_meta_data['version'] = ""
#         page_meta_data['page_number'] = ""
#         version = "None"
#         page_number = 1
#         try:
#             #acord_form_cord_tuple = (84,3728,600,3872) #x1,y1,x2,y2
#             version_location_identifier = 0 # 0-not matched, 1-first page, 2- other pages
#             acord_form_cord_tuple_1 = (84,3724,596,3768) #page 1
#             acord_form_cord_tuple_2 = (84,3780,596,3836) #page > 1
#             lines_data = page_data[1]['lines']
#             for line in lines_data:
#                 line_content = lines_data[line]["data"]
#                 line_bounding_box = lines_data[line]['Box']
                
#                 poly_x1 = line_bounding_box[0][0]
#                 poly_y1 = line_bounding_box[0][1]
#                 poly_x2 = line_bounding_box[2][0]
#                 poly_y2 = line_bounding_box[2][1]

#                 #line_cord_tuple = (poly_x1,poly_y1,poly_x2,poly_y2)
#                 #iou = self.bb_intersection_over_elabel(boxA=acord_form_cord_tuple ,boxB=line_cord_tuple)
#                 #if iou > 0.8:
#                 #    print(line_content)
#                 #    isThisVersion = re.search("^ACORD\s[0-9]{1,}\s[A-Z\s]{0,3}\(.*\)",line_content)
#                 #    print('isThisVersion')
#                 #    print(isThisVersion)
#                 #    if isThisVersion:
#                 #        print(line_content)
#                 #        page_aligned_status = True # if we get form version

#                 isThisVersion = re.search("^ACORD\s[0-9]{1,}\s[A-Z\s]{0,3}\(.*\)",line_content)
#                 if isThisVersion:
#                     line_content = line_content.split(" ")
#                     version = "".join(line_content)
#                     line_cord_tuple = (poly_x1,poly_y1,poly_x2,poly_y2)
#                     iou = self.bb_intersection_over_elabel(boxA=acord_form_cord_tuple_1 ,boxB=line_cord_tuple)
#                     if iou > 0.6:
#                         version_location_identifier = 1
#                     else:
#                         iou = self.bb_intersection_over_elabel(boxA=acord_form_cord_tuple_2 ,boxB=line_cord_tuple)
#                         if iou > 0.6:
#                             version_location_identifier = 2
                
#                 elif re.search("^Page\s[1-9]{1,}\sof\s[1-9]{1,}",line_content):
#                     page_number = line_content[5]
                
#             if version != "None":
#                 page_meta_data['version'] = version
#                 page_meta_data['page_number'] = page_number

#             if version != "None" and version_location_identifier == 1 and int(page_number) == 1: #page 1 case
#                 page_aligned_status = True
            
#             if version != "None" and version_location_identifier == 2 and int(page_number) > 1: #page 2 case
#                 page_aligned_status = True

#             return page_aligned_status, page_meta_data
        
#         except Exception as e:
#             return False , {}


#     def get_acord_form_version_and_page_number(self,img_path):
#         page_meta_data = dict()
#         page_meta_data['version'] = ""
#         page_meta_data['page_number'] = ""
#         version = "None"
#         page_number = 1
#         try:
#             page_data = self.analyze_page(img_path)  # if failed from form regonizer side, try one more time
#         except:
#             page_data = self.analyze_page(img_path)

#         page_data = page_data[1]['lines']
#         for idx,data in page_data.items():
#             line_data = data["data"]
#             isThisVersion = re.search("^ACORD\s[0-9]{1,}\s[A-Z\s]{0,3}\(.*\)",line_data)
#             if isThisVersion:
#                 line_data = line_data.split(" ")
#                 version = "".join(line_data)
#             elif re.search("^Page\s[1-9]{1,}\sof\s[1-9]{1,}",line_data):
#                 page_number = line_data[5]
#         if version != "None":
#             page_meta_data['version'] = version
#             page_meta_data['page_number'] = page_number
    
#         return page_meta_data


#     def get_acord_form_elabels(self,acord_form_version,page_number):
#         cords_data = sqlData(acord_form_version,page_number)
#         form_cords = cords_data[1]
#         return form_cords


#     def analyze_page(self,img_path):
#         page_data = analyze_page_data(img_path)
#         return page_data


#     def bb_intersection_over_elabel(self,boxA, boxB):
#         # determine the (x, y)-coordinates of the intersection rectangle
#         xA = max(boxA[0], boxB[0])
#         yA = max(boxA[1], boxB[1])
#         xB = min(boxA[2], boxB[2])
#         yB = min(boxA[3], boxB[3])
#         # compute the area of intersection rectangle
#         interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)
#         # compute the area of both the prediction and ground-truth
#         # rectangles
#         boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
#         boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)
#         # compute the intersection over union by taking the intersection
#         # area and dividing it by the sum of prediction + ground-truth
#         # areas - the interesection area
#         #iou = interArea / float(boxAArea + boxBArea - interArea)
#         # return the intersection over union value
        
#         iou = interArea / boxBArea
#         # return the intersection over elabel value
#         return iou


#     def get_other_parent_cord_elabels_data(self,elabels,page_data,elabel_other_parent_cord_elabels_id_tuple):
#         other_parent_cord_elabels_data = list()
#         for elabel in elabels:
#             elabel_data = str()
#             elabel_id = elabel[0]
#             lines_data = page_data[1]['words']
            
#             if str(elabel_id) in elabel_other_parent_cord_elabels_id_tuple:
#                 elabel_cord = elabel[2]
#                 if isinstance(elabel_cord, type(None)):
#                     continue

#                 elabel_field_type = elabel[4]

#                 for line in lines_data:
#                     line_cord_tuple = ""
#                     elabel_cord_tuple = ""
#                     line_content = lines_data[line]["data"]
#                     line_bounding_box = lines_data[line]['Box']

#                     poly_x1 = line_bounding_box[0][0]
#                     poly_y1 = line_bounding_box[0][1]
#                     poly_x2 = line_bounding_box[2][0]
#                     poly_y2 = line_bounding_box[2][1]

#                     if (poly_x1>poly_x2):
#                         poly_x1,poly_x2 = poly_x2,poly_x1

#                     if (poly_y1>poly_y2):
#                         poly_y1,poly_y2 = poly_y2,poly_y1

#                     line_cord_tuple = (poly_x1,poly_y1,poly_x2,poly_y2)

#                     if isinstance(elabel_cord, str):
#                         elabel_cord = elabel_cord.split(",")
                        
#                     x1 = int(elabel_cord[0])*5
#                     y1 = 3960 - (int(elabel_cord[3])*5)
#                     x2 = int(elabel_cord[2])*5
#                     y2 = 3960 - (int(elabel_cord[1])*5)
#                     elabel_cord_tuple = (x1,y1,x2,y2)

#                     if line_cord_tuple != "" and elabel_cord_tuple != "":
#                         iou = self.bb_intersection_over_elabel(boxA=elabel_cord_tuple,boxB=line_cord_tuple)
#                         if str(elabel_field_type).strip().lower() == "checkbox":
#                             if iou > 0.2:
#                                 other_parent_cord_elabels_data.append(line_content)       
#                         else:
#                             if iou > 0.7:
#                                 other_parent_cord_elabels_data.append(line_content)

#         return other_parent_cord_elabels_data


#     def extract_elabels_data(self,elabels,page_data):
#         elabels_data = dict()
#         elabel_parent_cord_tuple_list = list()
#         words_data = page_data[1]['words']
#         common_parent_data_list = list()
#         for elabel in elabels:
#             elabel_data = list()
#             elabel_cord_data = list()
#             elabel_cord_checkbox_data = str()
#             elabel_id = elabel[0]
#             elabel_field_name = elabel[1]
#             elabel_cord = elabel[2]
#             if isinstance(elabel_cord, type(None)):
#                 elabel_cord = ""

#             elabel_parent_cord = elabel[3]
#             if isinstance(elabel_parent_cord, type(None)):
#                 elabel_parent_cord = ""
            
#             elabel_field_type = elabel[4]
#             elabel_surpress_text = elabel[5]
#             if isinstance(elabel_surpress_text, type(None)):
#                 elabel_surpress_text = ""

#             if elabel_surpress_text != "":
#                 try:
#                     elabel_surpress_text_list = json.loads(elabel_surpress_text)  #convert str to list
#                 except Exception as e:
#                     elabel_surpress_text_list = list()
#             else:
#                 elabel_surpress_text_list = list()

#             elabel_surpress_word_list = list()
#             for elabel_surpress in elabel_surpress_text_list:
#                 elabel_surpress_word_list += str(elabel_surpress).split(" ")

#             elabel_other_parent_cord_elabels_id = elabel[6]
#             if isinstance(elabel_other_parent_cord_elabels_id, type(None)):
#                 elabel_other_parent_cord_elabels_id = ""

#             #if elabel_parent_cord != "" and elabel_other_parent_cord_elabels_id != "": # case 4(i),8
#             #    elabel_other_parent_cord_elabels_id_tuple = elabel_other_parent_cord_elabels_id.split(",")
#             #    elabel_other_parent_cord_elabels_list = self.get_other_parent_cord_elabels_data(elabels,page_data,elabel_other_parent_cord_elabels_id_tuple)
#             #else:
#             #    elabel_other_parent_cord_elabels_list = list()

#             elabel_cord_tuple = ""
#             elabel_parent_cord_tuple = ""

#             if elabel_parent_cord != "":
#                 if isinstance(elabel_parent_cord, str):
#                     elabel_parent_cord = elabel_parent_cord.split(",")
                
#                 x1 = int(elabel_parent_cord[0])
#                 y1 = int(elabel_parent_cord[1])
#                 x2 = int(elabel_parent_cord[2])
#                 y2 = int(elabel_parent_cord[3])
#                 elabel_parent_cord_tuple = (x1,y1,x2,y2)
                
#             if elabel_cord != "":
#                 if isinstance(elabel_cord, str):
#                     elabel_cord = elabel_cord.split(",")
                
#                 x1 = int(elabel_cord[0])*5
#                 y1 = 3960 - (int(elabel_cord[3])*5)
#                 x2 = int(elabel_cord[2])*5
#                 y2 = 3960 - (int(elabel_cord[1])*5)
#                 elabel_cord_tuple = (x1,y1,x2,y2)

#             elabel_cord_checkbox_data = str()
#             for word_id, word in enumerate(words_data):
#                 word_content = words_data[word]["data"]
#                 word_content = re.sub(' {2,}', ' ', word_content)
#                 word_content = word_content.strip()

#                 word_bounding_box = words_data[word]['Box']

#                 poly_x1 = word_bounding_box[0][0]
#                 poly_y1 = word_bounding_box[0][1]
#                 poly_x2 = word_bounding_box[2][0]
#                 poly_y2 = word_bounding_box[2][1]

#                 if (poly_x1>poly_x2):
#                     poly_x1,poly_x2 = poly_x2,poly_x1

#                 if (poly_y1>poly_y2):
#                     poly_y1,poly_y2 = poly_y2,poly_y1

#                 word_cord_tuple = (poly_x1,poly_y1,poly_x2,poly_y2)

                
#                 if str(elabel_field_type).strip().lower() == "checkbox":
#                     iou = self.bb_intersection_over_elabel(boxA=elabel_cord_tuple,boxB=word_cord_tuple)
#                     if iou > 0.2:
#                         elabel_cord_checkbox_data+=str(word_content)

#                 elif elabel_parent_cord_tuple != "":   # case 1,2,3,4(ii),6,7,4(i),8
#                     iou = self.bb_intersection_over_elabel(boxA=elabel_parent_cord_tuple,boxB=word_cord_tuple)
#                     iou2 = self.bb_intersection_over_elabel(boxA=elabel_cord_tuple,boxB=word_cord_tuple)
#                     word_not_assigned = True
#                     for common_data in common_parent_data_list:
#                         if word_id == common_data[0] and elabel_parent_cord_tuple == common_data[1] and elabel_field_name != common_data[2]:
#                             word_not_assigned = False
                    
                    
#                     if elabel_parent_cord != elabel_cord:  # to bypass mannual entries
#                         if iou > 0.8 and iou2 > 0.2 and word_not_assigned:                          
#                             elabel_data.append(word_content)
#                             common_parent_data_list.append((word_id, elabel_parent_cord_tuple,elabel_field_name,word_content))
#                     else:
#                         if iou > 0.8 and word_not_assigned:                          
#                             elabel_data.append(word_content)
#                             common_parent_data_list.append((word_id, elabel_parent_cord_tuple,elabel_field_name,word_content))

#                 elif elabel_cord_tuple != "":  # other cases
#                     iou = self.bb_intersection_over_elabel(boxA=elabel_cord_tuple,boxB=word_cord_tuple) 
#                     if iou > 0.8:
#                         elabel_data.append(word_content)


#             if str(elabel_field_type).strip().lower() == "checkbox":
#                 elabel_cord_checkbox_data = elabel_cord_checkbox_data.replace(" ","")
#                 if elabel_cord_checkbox_data != "":
#                     elabels_data[elabel_field_name] = True
#                 else:
#                     elabels_data[elabel_field_name] = False
            
#             else:
#                 elabel_str_data = (" ".join(map(str, elabel_data))).strip()
#                 for surpress_text in elabel_surpress_word_list:
#                     if surpress_text in elabel_str_data:
#                         elabel_str_data = str(elabel_str_data).replace(surpress_text,"",1)

#                 if 'postalcode' in str(elabel_field_name).lower() and 'address' in str(elabel_field_name).lower():
#                     elabel_str_data = self.detect_postal_code(elabel_str_data,common_parent_data_list,elabel_parent_cord_tuple,elabels_data)
                
#                 if 'provincecode' in str(elabel_field_name).lower() and 'address' in str(elabel_field_name).lower():
#                     province_code = self.detect_province_code(elabel_str_data,common_parent_data_list,elabel_parent_cord_tuple,elabels_data)
#                     if province_code != False:
#                         elabel_str_data = province_code

#                 if 'cityname' in str(elabel_field_name).lower() and 'address' in str(elabel_field_name).lower():
#                     city_name = self.detect_city_name(elabel_str_data,common_parent_data_list,elabel_parent_cord_tuple,elabels_data)
#                     elabel_str_data = city_name


#                 #elabel_str_data_split = elabel_str_data.split(" ")
#                 #elabel_str_data_list = list()
#                 #for elabel_str_word in elabel_str_data_split:
#                 #    if elabel_str_word not in elabel_other_parent_cord_elabels_list:
#                 #        elabel_str_data_list.append(elabel_str_word)

#                 #elabels_data[elabel_field_name] = (" ".join(map(str, elabel_str_data_list))).strip()
#                 elabels_data[elabel_field_name] = elabel_str_data.strip()

#         return elabels_data


#     def detect_postal_code(self,elabel_str_data=str(),common_parent_data_list=list(),elabel_parent_cord_tuple=tuple(),elabels_data=dict()):
#         try:
#             postal_code = str()
#             ispostalcode = re.search("(\d{5})([- ])?(\d{4})?",elabel_str_data)
#             if ispostalcode:
#                 postal_code = ispostalcode.group()
#                 return postal_code
#             else:
#                 for common_data in common_parent_data_list[::-1]:
#                     if elabel_parent_cord_tuple == common_data[1]:
#                         data_str = common_data[3]
#                         ispostalcode = re.search("(\d{5})([- ])?(\d{4})?",data_str)
#                         if ispostalcode:
#                             postal_code = ispostalcode.group()
#                             other_elabel_name = common_data[2]
#                             try:
#                                 elabels_data[other_elabel_name] = str(elabels_data[other_elabel_name]).replace(postal_code,"").strip()
#                             except:
#                                 pass
#                             return postal_code
            
#             return elabel_str_data
    
#         except:
#             return elabel_str_data

    
#     def detect_province_code(self,elabel_data=list(),common_parent_data_list=list(),elabel_parent_cord_tuple=tuple(),elabels_data=dict()):
#         try:
#             us_provision_code_list = [ 'AK', 'AL', 'AR', 'AZ', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA',
#                                         'HI', 'IA', 'ID', 'IL', 'IN', 'KS', 'KY', 'LA', 'MA', 'MD', 'ME',
#                                         'MI', 'MN', 'MO', 'MS', 'MT', 'NC', 'ND', 'NE', 'NH', 'NJ', 'NM',
#                                         'NV', 'NY', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX',
#                                         'UT', 'VA', 'VT', 'WA', 'WI', 'WV', 'WY']
            
#             us_provision_name_list = ["Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut",
#                                     "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", 
#                                     "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan",
#                                     "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire",
#                                     "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio", 
#                                     "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
#                                     "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia", 
#                                     "Wisconsin", "Wyoming"]
            

#             province_code = str()

#             for data_item in elabel_data:
#                 data_item = str(data_item).replace(",","").upper().strip()
#                 if data_item in us_provision_code_list:
#                     province_code = data_item
#                     return province_code
                
#                 if data_item in us_provision_name_list:
#                     province_code = data_item
#                     return province_code

#             for common_data in common_parent_data_list[::-1]:
#                 if elabel_parent_cord_tuple == common_data[1]:
#                     data_str = common_data[3]
#                     data_str = str(data_str).replace(",","").upper().strip()
#                     if data_str in us_provision_code_list:
#                         province_code = data_str
#                         other_elabel_name = common_data[2]
#                         try:
#                             elabels_data[other_elabel_name] = str(elabels_data[other_elabel_name]).replace(province_code,"").strip()
#                         except:
#                             pass
#                         return province_code
                    
#                     if data_str in us_provision_name_list:
#                         province_code = data_str
#                         other_elabel_name = common_data[2]
#                         try:
#                             elabels_data[other_elabel_name] = str(elabels_data[other_elabel_name]).replace(province_code,"").strip()
#                         except:
#                             pass
#                         return province_code
            
#             return False
    
#         except:
#             return False


#     def detect_city_name(self,elabel_str_data=str(),common_parent_data_list=list(),elabel_parent_cord_tuple=tuple(),elabels_data=dict()):
#         try:
#             url = config('DOC_READER_SUPPORT_API_DETECT_CITIES_FROM_TEXT_URL')
#             if elabel_str_data.strip() !="":
#                 payload={'text': elabel_str_data}
#                 response = requests.request("POST", url, data=payload,verify=False)
#                 cities_list = json.loads(response.text)
#                 cities_list = list(cities_list)
#                 if len(cities_list):
#                     if len(cities_list[0]) < len(elabel_str_data):
#                         return elabel_str_data
                        
#                     return cities_list[0]
            
#             elif len(common_parent_data_list):
#                 common_parent_elabel_list = list()
#                 for common_data in common_parent_data_list[::-1]:
#                     if elabel_parent_cord_tuple == common_data[1]:
#                         elabel_field_name = common_data[2]
#                         if elabel_field_name not in common_parent_elabel_list:
#                             common_parent_elabel_list.append(elabel_field_name)

#                 for common_elabel_field_name in common_parent_elabel_list:
#                     common_parent_elabel_data = elabels_data[common_elabel_field_name]
#                     payload={'text': common_parent_elabel_data}
#                     response = requests.request("POST", url, data=payload,verify=False)
#                     cities_list = json.loads(response.text)
#                     cities_list = list(cities_list)
#                     if len(cities_list):
#                         try:
#                             elabels_data[common_elabel_field_name] = str(elabels_data[common_elabel_field_name]).replace(cities_list[0],"").replace(","," ").strip()
#                         except:
#                             pass
#                         return cities_list[0]
                    
                        
#             return elabel_str_data
        
#         except:
#             return elabel_str_data
    

#     def align_pdf_image_with_reference_image(self,pdf_image_path,acord_form_version,acord_form_page_number):
#         try:
#             acord_form_version = str(acord_form_version).replace("/","")
#             reference_image_path = "acord_forms/" + acord_form_version +"/" + "page" + str(acord_form_page_number) + ".jpg"
#             storage_obj = azure_storage_account()
#             if storage_obj.folder_file_exists(reference_image_path) and storage_obj.folder_file_exists(pdf_image_path):
#                 server = config('SERVER_STAGE')
#                 alignment_status = self.call_alignment_api(image_path=pdf_image_path,template_path=reference_image_path, server=server)
#                 #align_images(pdf_image_path,reference_image_path)
#                 return alignment_status
            
#             return False
        
#         except Exception as e:
#             return False

#     def call_alignment_api(self,image_path="",template_path="",server=""):
#         url = "https://docreader-api-support.webnerserver.com/v1/align-image"
#         payload={'image_path': image_path,
#         'template_path': template_path,
#         'server': server}
#         files=[]
#         headers = {}
#         response = requests.request("POST", url, headers=headers, data=payload, files=files, verify=False)
#         return True

#     def detect_acord_form(self,image_path):
#             url = config("DOC_READER_SUPPORT_API_DETECT_ACORD_FORM_URL")
#             server = config("SERVER_STAGE")
#             payload={'image_path': image_path,
#             'server': server}
#             files=[
#             ]
#             headers = {}
#             response = requests.request("POST", url, headers=headers, data=payload, files=files, verify=False)

#             print("response", response.text)
#             return response.text

# if __name__ == "__main__":
#     # obj = Doc_scanner('/home/webner/Documents/page1.jpg')
#     # obj.page_scan('/home/webner/Documents/page1.jpg')
#     # obj.detect_acord_form('/home/webner/Documents/page1.jpg')
#     pass
