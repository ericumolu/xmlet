#!/usr/local/bin/python3.3

#    This file is part of xmlet.
#
#    xmlet is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    xmlet is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with xmlet.  If not, see <http://www.gnu.org/licenses/>.

import os
import re
import sys

#logfile = open('logfile2.log','a')

#class to track the current posistion during xml object branch navigation
#NodeTracker object is passed down from the top to bottom in an xml object during navigation
class NodeTracker:
    def __init__(self):
        self.node_map = [None]
        self.node_map[0] = [0]
        self.matches = []
        self.level = 0
        self.last = 0
        self.node_count = 0
        self.display_text = ""
        self.tab_spacing = 0
        self.element_line_spacing = 0

    def set_spacing(self,tab_spacing,element_line_spacing):
        self.tab_spacing = tab_spacing
        self.element_line_spacing = element_line_spacing

    def set_map_row(self):
        if not self.level:
            return 0

        self.node_map.append([])

        if (self.level > self.last):
            child = 0
        elif(self.level == self.last):
            child = self.node_map[-2][self.last] + 1
        elif (self.level < self.last):
            child = self.node_map[-2][self.level] + 1

        for position in range(self.level):
            self.node_map[-1].append(self.node_map[-2][position])
        self.node_map[-1].append(child)

class Component:
    def __init__(self):
        self.attribute = []
        self.element = ""
        self.content = ""
        self.end_slash = 0
        self.comment_value = ""

class Attribute:
    def __init__(self,attribute="", value=""):
        self.special_attr = ['class']
        self.name = attribute
        self.value = []
        self.quote = ""
        self.count = 0
        self.remove = 0
        if value:
            self.set_value(value)

    def set_value(self,value):
        if ('\"' or "\'") == value[0]:
            self.quote = value[0]

            if self.name in self.special_attr:
                self.value.extend(re.split('\s+',value[1:-1]))
            else:
                self.value = [value[1:-1]]
        else:
            self.value = [value]

    def copy(self):
        attribute = Attribute(self.name)
        attribute.value = self.value[:]
        attribute.quote = self.quote
        attribute.special_attr = self.special_attr[:]
        attribute.count = self.count
        return attribute

class Section:
    def __init__(self,end_tag):
        self.end_tag = end_tag
 
class XmlNode:
#create blank_node at top
#comment need be on same at html
#dont print blank node

    def __init__(self,element="",content="",tab_spacing=5,element_line_spacing=1):
#       def __init__(self,element="",content="",tab_spacing=0,element_line_spacing=0):
        self.display_text = ""
        self.position = 0
        self.index = 0
        self.line = ""
        self.template_file = ""
        self.remove = 0
        self.end_slash = 0
        self.start_tag_present = 1
        self.display_show = 1
        self.end_tag_present = 1
        self.parent = None
        self.node_count = 0
        self.display_type = ""
        self.remove = 0
        self.content = ""
        self.after_content = ""
        self.comment_value = ""
        self.element = element
        self.content = content
        self.attribute = {}
        self.xml_node = []
        #set the initial match so get_foo methods can work from the start
        self.matches = [self]
        self.tab_spacing = tab_spacing
        self.element_line_spacing = element_line_spacing
        self.comment = {'open':'!--','close':'--'}
        self.group_set = {"\'":0, '"':0, '(':0, '{':0, '[':0,self.comment['open']:0,self.comment['close']:0}
        self.open = "<"
        self.close = ">"
        self.end_open = self.open + '/'
        #need descriptions for read_type 1 and 2
        self.read_type = 1
        self.special_tag = ['script']
        #dictionary name is also start_tag name when calling check_special_section()
        self.expand_att_value = "expand"

    def set_element(self,element):
        matches_copy = self.matches[:]
        self.clear()

        for match in matches_copy:
            match.element = element
        return 1

    def get_attribute(self, attribute):
        matches_copy = self.matches[:]
        self.clear()

        for match in matches_copy:
            if attribute in match.attribute:
                return " ".join(match.attribute[attribute].value)
            else:
                return None

    def set_content(self,content, location=0):
        matches_copy = self.matches[:]
        self.clear()

        for match in matches_copy:
            if location == 0:
                match.content = content
            elif location == -1:
                if not len(match.xml_node):
                    match.content = content
                else:
                    match.xml_node[location].after_content = content
            else:
                match.xml_node[location - 1].after_content = content
        return 1

    #does not return self.after_content
    def get_content(self,location=0):
        matches_copy = self.matches[:]
        self.clear()

        content_list = []
        for match in matches_copy:
            if location == 0:
                content_list.append(match.content)
            elif location == -1:
                if not len(match.xml_node):
                    content_list.append(match.content)
                else:
                    content_list.append(match.xml_node[location].after_content)
            else:
                content_list.append(match.xml_node[location - 1].after_content)

        return content_list


    def remove_end_element(self):
        self.remove_element_part(1)

    def remove_start_element(self):
        self.remove_element_part(0)

    #method to reset node branch under the element that is modfied,give children back to the parent of modified node
    def remove_element_part(self, start):
        matches_copy = self.matches[:]
        self.clear()

        for match in matches_copy:
            for node in match.xml_node:
                match.parent.add_child('','',match.position + start)
                match.parent.xml_node[match.position + start].copy(node)
                start += 1

            match.xml_node = []
            match.reset_child_position(match.parent)

            if start:
                match.end_tag_present = 0
            else:
                match.start_tag_present = 0

    def reset_child_position(self,parent):
        count = 0
        for node in parent.xml_node:
            node.position = count
            count += 1 

    def set_after_content(self,after_content):
        matches_copy = self.matches[:]
        self.clear()

        for match in matches_copy:
            match.after_content = after_content
        return 1

    def add_attribute(self,attribute,value):
        matches_copy = self.matches[:]
        self.clear()

        for match in matches_copy:
            if attribute in match.attribute:
                count = match.attribute[attribute].count
                match.attribute[attribute].set_value(value)
            else:
                count = len(match.attribute) - 1
                match.attribute[attribute] = Attribute(attribute,value)
            match.attribute[attribute].count = count
        return 1

    def set_attribute(self,attribute,value):
        self.add_attribute(attribute,value)

        return 1

    def sort_attribute(self):
        return sorted(self.attribute.keys(), key=lambda x: self.attribute[x].count )

    def add_child(self, child_element="",child_content="",position=-1):
        matches_copy = self.matches[:]
        self.clear()

        for match in matches_copy:
            if position < 0:
                position = len(match.xml_node)
            if child_element and child_element[0] == '/':
                match.xml_node.insert(position,XmlNode(child_element[1:],child_content))
                match.xml_node[-1].start_tag_present = 0
            else:
                match.xml_node.insert(position,XmlNode(child_element,child_content))
            match.xml_node[-1].parent = match
            match.xml_node[-1].position = (len(match.xml_node) - 1)

        return 1

    def check_element(self, element,check_type=0):
        if check_type == 0:
            if re.search('^[a-zA-Z/]',element):
                return 1
            else:
                return 0

        if check_type == 1:
            if re.search('^[0-9a-zA-Z/]',element):
                return 1
            else:
                return 0

    def set_component(self):
        components = []
        inside = 0
        quote_on = 0
        element_off = 0
        value_on = 0
        hold = []
        quote = ""
        special = ""
        comment_off = 0
        self.index = 0
        while self.index < len(self.line):
            char = self.line[self.index]

#               logfile.write( "\nchar:" + char)
            if char == '<':
 #                  logfile.write("\nif char == '<':")
                if inside:
#                       logfile.write("\nif inside:")
                    if value_on:
                        if self.group():
                            hold.append(char)
#                           else:
#                               logfile.write( "\n???:"+char)
                    else:
                        hold.append(char)
#                           logfile.write( "\n???:"+char)
                else:
                    if self.group():
#                           logfile.write( "\nself.group()")
                        hold.append(char)
                    else:
#                           logfile.write( "\nelse inside:")
                        if hold:
#                               logfile.write( "\ncontent:" + hold[0])
                            components.append(Component())
                            components[-1].content = ''.join(hold)
                            hold = []
                        inside = 1
            elif char == '>':
#                   logfile.write( "\nelif char == '>':")
                if inside:
#                       logfile.write( "\nif inside:")
                    if value_on:
#                           logfile.write( "\nif value_on:")
                        if self.group():
#                               logfile.write( "\nif self.group():")
                            hold.append(char)
                        else:
#                               logfile.write( "\nelse self.group():")
                            if hold:
                                components[-1].attribute[-1].set_value(''.join(hold))
#                                   logfile.write( "\nattribute value:" + hold[0])
                            inside = 0
                            value_on = 0
                            hold = []
                            element_off = 0

                    elif element_off:
#                           logfile.write( "\nelif element_off:")
                        if self.group():
                            hold.append(char)
                        else: 
                            if hold:
#                                   logfile.write( "\nif hold[0]:")
                                if ''.join(hold).endswith('/'):
#                                       logfile.write( "\nif '/' == hold[0][-1]:")
                                    components[-1].end_slash = 1
                                else:
#                                       logfile.write( "\nincomplate attribute?:" + hold[0])
                                    hold.append(''.join(hold))
                            hold = []
                            inside = 0
                            element_off = 0
#                               logfile.write( "\noutside:")

                    elif not element_off:
#                           logfile.write( "\nelif not element_off:")

                        if self.group():
                            hold.append(char)

                        elif hold:
                            if comment_off:
                                components.append(Component())
                                components[-1].comment_value = ''.join(hold)
                                comment_off = 0

                            elif self.check_element(''.join(hold)):
#                                   logfile.write( "\nInside off")
                                if special:
                                    if ''.join(hold)[1:] == special:
#                                           logfile.write( "\nclose special element:" + hold[0])
                                        components.append(Component())
                                        components[-1].element = ''.join(hold)
                                        special = ""
                                    else:
                                        self.clear_group()
                                        inside = 0
                                        hold = ['<' + ''.join(hold) + char]
                                        components.append(Component())
                                        components[-1].content = ''.join(hold)
                                else:
                                    if self.check_special(''.join(hold)):
#                                           logfile.write( "\nopen special element:" + hold[0])
                                        special = ''.join(hold)
                                    components.append(Component())
                                    components[-1].element = ''.join(hold)
#                                       logfile.write( "\nelement:" + hold[0])
                            else:
                                hold = ['<' + ''.join(hold) + char]
                                components.append(Component())
                                components[-1].content = ''.join(hold)
                            hold = []
                            inside = 0
                            
                else:
#                       logfile.write( "\nelse:")
                    hold.append(char)
            elif char == ' ':
#                   logfile.write( "\nelif char == ' ':")
                if inside:
#                       logfile.write( "\nif inside")
                    if value_on:
#                           logfile.write( "\nif value_on:")
                        if self.group():
                            hold.append(char)
                        else:
                            if hold:
                                components[-1].attribute[-1].set_value(''.join(hold))
#                                   logfile.write( "\nattribute value:" + hold[0])
                                hold = []
                                value_on = 0

                    elif element_off:
#                           logfile.write( "\nelif element_off:")
                        if hold:
#                               logfile.write( "\nincomplete attribute?:" + hold[0])
#                               logfile.write( "\nhold:")
                            hold.append(''.join(hold))
                            hold = []

                    elif self.group():
                        hold.append(char)

                    else:
#                           logfile.write( "\nelse:")
                        if hold:
                            if self.check_element(''.join(hold)):
                                if special:
                                    if ''.join(hold)[1:] == special:
#                                           logfile.write( "\nclose special element:" + hold[0])
                                        components.append(Component())
                                        components[-1].element = ''.join(hold)
                                        special = ""
                                    else:
                                        hold = ['<' + ''.join(hold) + char]
                                        components.append(Component())
                                        components[-1].content = ''.join(hold)
                                        inside = 0
                                        self.clear_group()
                                else:
                                    if self.check_special(''.join(hold)):
                                        special = ''.join(hold)
                                    components.append(Component())
                                    components[-1].element = ''.join(hold)
#                                       logfile.write( "\nelement:" + hold[0])
                                    element_off = 1
                                hold = []
                            else:
#                                   logfile.write( "\nInside off")
                                inside = 0
                                hold = ['<' + ''.join(hold) + char]
                                #get rid of any group sets if not really an element,read_type == 1 ,element matching only
                                if self.read_type == 1:
                                    self.clear_group()

                else:
                    hold.append(char)

            elif char in "\"\'":
#                   logfile.write( "\nelif char == \"\'\" or char == \'\"\':")

                hold.append(char)

                if inside:
                    if self.read_type == 1 or self.read_type == 2:
                        result = self.group(char,''.join(hold))

                    if value_on:
                        if result == 0:
#                               logfile.write( "\nattribute value:" + hold[0])
                            components[-1].attribute[-1].set_value(''.join(hold))
                            hold = []
                            value_on = 0
                else:
                    if self.read_type == 2:
                        self.group(char)

            elif char in '[](){}':
#                   logfile.write( "\nelif char in '[](){}")
                
                hold.append(char)

                if inside:
                    if self.read_type == 1 or self.read_type == 2:
                        self.group(char)
                else:
                    if self.read_type == 2:
                        self.group(char)

            elif char in self.comment['open'][0] + self.comment['close'][0]:
                if self.group():
#                       logfile.write( "\nif result")
                    if self.group(char) > 0:
#                           logfile.write( "\ncoment off")
                        comment_off = 1
                    else:
                        hold.append(char)
                else:
#                       logfile.write( "\nelse result")
                    if self.group(char) > 0:
#                           logfile.write( "\ncoment on")
                        pass
                    else:
                        hold.append(char)

            elif char == '=':
#                   logfile.write( "\nelif char == '=':")
                if inside:
                    if value_on:
                        hold.append(char)
                    elif self.group():
                        hold.append(char)
#                           value_on = 1
                    elif element_off:
                        if hold:
                            components[-1].attribute.append(Attribute(''.join(hold)))
#                               logfile.write( "\nattribute:"+hold[0])
                            hold = []

                        value_on = 1
                    else:
                        hold.append(char)
                else:       
                    hold.append(char)

            else:
#                   logfile.write( "\nelse:")
                hold.append(char)

#               logfile.write( "\ninside:"+str(inside))
#               logfile.write( "\nhold[0]:"+hold[0]+':')
    #           logfile.write( "\nhold:"+str(hold))
#               self.show_group()
            self.index += 1 
        return components

    def group(self,group_type="",hold=""):
        if group_type:
            if group_type == "\"" and not self.group_set["\'"]:
                if len(hold) == 0 or (len(hold) > 0 and hold[0] == group_type): 

                    if self.group_set[group_type]:
                        self.group_set[group_type] = 0
                        return 0
                    else:
                        self.group_set[group_type] = 1
                        return 1
                else:
                    return -1

            elif group_type == "\'" and not self.group_set["\""]:
                if len(hold) == 0 or (len(hold) > 0 and hold[0] == group_type):

                    if self.group_set[group_type]:
                        self.group_set[group_type] = 0
                        return 0
                    else:
                        self.group_set[group_type] = 1
                        return 1
                else:
                    return -1

            elif group_type in "{([" and not self.group():
                self.group_set[group_type] += 1

            elif group_type == self.comment['open'][0] and not self.group():
                if self.line[self.index:self.index+len(self.comment['open'])] == self.comment['open']:
                    self.group_set[self.comment['open']] += 1
                    self.index += len(self.comment['open']) - 1
                    return 1
                else:
                    return 0
            elif group_type == self.comment['close'][0] and self.group_set[self.comment['open']]:
                if self.line[self.index:self.index+len(self.comment['close'] + self.close)] == self.comment['close'] + self.close:
                    self.group_set[self.comment['open']] -= 1
                    self.index += len(self.comment['close']) - 1
                    return 1
                else:
                    return 0
            elif group_type == "}" and self.group_set["{"]:
                    self.group_set["{"] -= 1

            elif group_type == ")" and self.group_set["("]:
                    self.group_set["("] -= 1

            elif group_type == "]" and self.group_set["["]:
                    self.group_set["["] -= 1
            else:
                return -1
        else:
            return sum([self.group_set[g_type] for g_type in self.group_set])

#       def show_group(self):
#           logfile.write('\n\n')
#           for g_type in self.group_set:
#               logfile.write('\n'+g_type+':'+str(self.group_set[g_type]))      

    def clear_group(self):
        for group_type in self.group_set:
            self.group_set[group_type] = 0  

    def find_end_element(self, components, position, element):
        end_element = re.compile('^ */' + re.escape(element) + ' *$')
        element = re.compile('^ *' + re.escape(element) + ' *$')
        
        element_count = 1
        end_element_count = 0
    
        for component in components[position + 1:]:
            if component.element:
                if element.search(component.element):
                    element_count += 1
                elif end_element.search(component.element):
                    end_element_count += 1
            if element_count == end_element_count:
                return 1
        return 0


    def check_special(self, element):
        if element in self.special_tag:
            return 1
        else:
            return 0

    #top element(first element in the tree will be blank)
    #if the inital data in the file isnt an element ex:doctype declaration, 
    #it will be set as content to the top, blank element and will be displayed as such in self.display()
    def read(self,template_file=""):
        if template_file:
            file = template_file
        else:
            file = self.template_file
        for line in open(file):
            self.line += line
        components = self.set_component()

#DEBUGGING ONLY
#           c = 0
#           for x in components:
#               logfile.write('\n\nAT:'+str(c))
#               logfile.write('\nelem:'+x.element+':')
#               logfile.write('\ncomment:'+x.comment_value+':')
#               if x.attribute:
#                   for y in x.attribute:
#                       logfile.write('\natt:'+str(y.name) + "="+str(y.value))
#               logfile.write('\ncont:'+x.content+':')
#               logfile.write('\nend_s:'+str(x.end_slash))
#               c += 1


        xml_nav = self

        xml_nav.open = ""
        xml_nav.close = ""
        xml_nav.end_open = ""

        position = 0

        for component in components:
            if component.element:
                if component.element.startswith('/'):
                    if component.element[1:] == xml_nav.element:
                        xml_nav = xml_nav.parent
                    else:
                        #ORPAN element
                        #remove '/' from component.element, will be added back at display()
                        xml_nav.add_child(component.element[1:])
                        xml_nav.xml_node[-1].start_tag_present = 0
                else:
                    xml_nav.add_child(component.element)
                    if self.find_end_element(components, position, component.element):
                        xml_nav = xml_nav.xml_node[-1]
                        xml_nav.end_tag_present = 1
                        
                        if component.attribute:
                            for att in component.attribute:
                                xml_nav.attribute[att.name] = Attribute() 
                                xml_nav.attribute[att.name] = att.copy()
                    else:
                        xml_nav.xml_node[-1].end_tag_present = 0
                        xml_nav.xml_node[-1].end_slash = component.end_slash
                        if component.attribute:
                            for att in component.attribute:
                                xml_nav.xml_node[-1].attribute[att.name] = Attribute()
                                xml_nav.xml_node[-1].attribute[att.name] = att.copy()
            elif component.content:
                if len(xml_nav.xml_node):
                    xml_nav.xml_node[-1].after_content += component.content
                else:
                    xml_nav.content += component.content
            elif component.comment_value:
                xml_nav.add_child()
                xml_nav.xml_node[-1].comment_value = component.comment_value
                xml_nav.xml_node[-1].start_tag_present = 0
                xml_nav.xml_node[-1].end_tag_present = 0
            position += 1

        self.clear()

    def copy(self, copy_source):
        if not len(copy_source.matches):
            copy_source.matches.append(copy_source)

        #make copy of match list of objects before wiping all variables in objects
        matches_copy = self.matches[:]

        for match in matches_copy:
            match.__init__()
            for copy_match in copy_source.matches:
                node_tracker = NodeTracker()
                match.copy_node(match,copy_match,node_tracker)
        copy_source.clear()
        self.clear()
        return 1

    def copy_node(self, copy_destination, copy_source,node_tracker):
        node_tracker.last = node_tracker.level
        node_tracker.level += 1

        if node_tracker.node_count > 0:
            if node_tracker.level > node_tracker.last:
                copy_destination.add_child()
                copy_destination.xml_node[-1].parent = copy_destination
                copy_destination = copy_destination.xml_node[-1]
            
            elif node_tracker.level < node_tracker.last:
                copy_destination = copy_destination.parent.parent
                copy_destination.add_child()
                copy_destination = copy_destination.xml_node[-1]            
            
            elif node_tracker.level == node_tracker.last:
                copy_destination = copy_destination.parent
                copy_destination.add_child()
                copy_destination = copy_destination.xml_node[-1]
        else:
            node_tracker.node_count += 1

        self.copy_variables(copy_destination, copy_source)
            
        for att in copy_source.attribute:
            copy_destination.attribute[copy_source.attribute[att].name] = Attribute()
            copy_destination.attribute[copy_source.attribute[att].name] = copy_source.attribute[att].copy()
        for node in copy_source.xml_node:
             node_tracker = node.copy_node(copy_destination ,node, node_tracker)
        node_tracker.last = node_tracker.level
        node_tracker.level -= 1

        return node_tracker

    def copy_variables(self,copy_destination, copy_source):
        copy_destination.element = copy_source.element
        copy_destination.content = copy_source.content
        copy_destination.after_content = copy_source.after_content
        copy_destination.end_tag_present = copy_source.end_tag_present
        copy_destination.start_tag_present = copy_source.start_tag_present
        copy_destination.end_slash = copy_source.end_slash
        copy_destination.comment_value = copy_source.comment_value

    def remove_element(self):
        matches_copy = self.matches[:]
        self.clear()

        for match in matches_copy:
            match.remove = 1
            if match.parent != None:
                offset = 0
                for node in range(len(match.parent.xml_node)):
                    if match.parent.xml_node[node - offset].remove:
                        match.parent.xml_node.pop(node - offset)
                        offset += 1
        return 1

    def remove_attribute(self,att_to_remove,value_to_remove=""):
        remove = []

        matches_copy = self.matches[:]
        self.clear()

        for match in matches_copy:
            offset = 0
            for attr in match.attribute:
                if attr == att_to_remove:
                    if value_to_remove:
                        value_offset = 0
                        value_index = 0
                        for value_index in range(len(match.attribute[attr].value)):
                            if match.attribute[attr].value[value_index - value_offset] == value_to_remove:
                                logfile.write('\nremove'+match.attribute[attr].value[value_index - value_offset])       
                                match.attribute[attr].value.pop(value_index - value_offset)
                                value_offset += 1

                        if not match.attribute[attr].value:
                            remove.append(attr)
                    else:
                        remove.append(attr)
        for attr in remove:
            del match.attribute[attr]

        return 1


    def add_parent(self,parent_element="", parent_content=""):
        matches_copy = self.matches[:]
        self.clear()

        for match in matches_copy:
            old = XmlNode()
            old.copy(match)
            match.__init__(parent_element, parent_content)
            match.add_child()
            match.xml_node[0].copy(old)
            match.xml_node[0].parent = match
        return 1

    #use reset to clear match list only,dont add self to match list
    def reset(self,to_reset):
        for reset in to_reset:
            while len(reset):
                reset.pop()

    #use clear, to clear match list and also add the top of the tree(ie:self) back to the match list to search from,for methods that do searching like get_element
    def clear(self):
        count = len(self.matches)
        self.reset([self.matches])
        self.matches.append(self)
        return count
        
    def get_element(self, element,element_number=None,max_depth=-1,expand=0):
        matches_copy = self.matches[:]
        self.reset([self.matches])

        for match in matches_copy:
            node_tracker = NodeTracker()

            if isinstance(element_number, int):
                self.matches.append(match.get_element_node(node_tracker,element,element_number,max_depth,expand).matches[element_number])
            else:
                self.matches.extend(match.get_element_node(node_tracker,element,element_number,max_depth,expand).matches)
    
        if not len(self.matches):
            return None

        return self

    def expand(self):
        expanded = 0

        for match in self.matches:
            expand = match.get_matches(0)[0].get_attribute(self.expand_att_value)
            element = match.get_matches()[0].element

            if expand:
                expand_node = XmlNode()
                expand_node.read(expand)

                if expand_node.get_element(element):
                    match.copy(expand_node)
                    expanded = 1
        self.clear()
        return expanded

    def get_element_data(self):
        matches_copy = self.matches[:]
        self.clear()

        for match in matches_copy:
            return match.content

    def get_matches(self, clear = 1):
        matches_copy = self.matches[:]
        if clear:
            self.clear()
        return matches_copy

    #return all child nodes of an element
    def get_children(self):
        matches_copy = self.matches[:]
        self.reset([self.matches])

        for match in matches_copy:
            for node in match.xml_node:
                self.matches.append(node)

        if not len(self.matches):
            return None

        return self


    def get_element_content(self, content, element_number=None, match_type=0):
        matches_copy = self.matches[:]
        self.reset([self.matches])

        for match in matches_copy:
            node_tracker = NodeTracker()

            if isinstance(element_number, int):
                self.matches.append(match.get_element_content_node(node_tracker,content,element_number,match_type).matches[element_number])
            else:
                self.matches.extend(match.get_element_content_node(node_tracker,content,element_number,match_type).matches)

        if not len(self.matches):
            return None
        
        return self
    
    #get element by content
    def get_element_content_node(self,node_tracker, content, element_number, match_type):
        #dont check against first match only children
        if node_tracker.node_count:
            #lower() for case insensitive searching
            if match_type == 0:
                if content.lower() == self.content.lower():
                    node_tracker.matches.append(self)
            elif match_type == 1:
                if content.lower() in self.content.lower():
                    node_tracker.matches.append(self)

        node_tracker.node_count += 1
        for node in self.xml_node:
            if isinstance(element_number, int):
                if element_number > -1 and ((len(node_tracker.matches) - 1) == element_number):
                    return node_tracker

            node_tracker = node.get_element_content_node(node_tracker, content, element_number, match_type)
        return node_tracker

    def get_element_attribute(self,attribute,value='',element_number=None,match_type=0):
        matches_copy = self.matches[:]
        self.reset([self.matches])

        for match in matches_copy:
            node_tracker = NodeTracker()

            if isinstance(element_number, int):
                self.matches.append(match.get_element_attribute_node(node_tracker,attribute,value,element_number,match_type).matches[element_number])
            else:
                self.matches.extend(match.get_element_attribute_node(node_tracker,attribute,value,element_number,match_type).matches)

        if not len(self.matches):
            return None

        return self

    def get_element_node(self, node_tracker, element, element_number,max_depth,expand):
        #dont check against first match only children
        if node_tracker.node_count:
            if (max_depth < 0) or ((max_depth > 0) and (node_tracker.level <= max_depth)):
                if expand:
                    self.expand()
                if element == "_match_" or (self.element == element):
                    node_tracker.matches.append(self)
            else:
                return node_tracker

        node_tracker.node_count += 1
        node_tracker.level += 1

        for node in self.xml_node:
            if isinstance(element_number, int):
                if element_number > -1 and ((len(node_tracker.matches) - 1) == element_number):
                    return node_tracker
            node_tracker = node.get_element_node(node_tracker,element,element_number,max_depth,expand)

        node_tracker.level -= 1

        return node_tracker

    def get_element_attribute_node(self,node_tracker,attribute,value,element_number,match_type):
        #dont check against first match only children
        if node_tracker.node_count:
            if value:
                if (value[0] and value[-1]) == ("\"" or "\'"):
                    value = value[1:-1]
                for attr in self.attribute:
                    if self.attribute[attr].name == attribute:
                        if match_type == 0:
                            for att_value in self.attribute[attr].value:
                                if value == att_value:
                                    node_tracker.matches.append(self)
                                    #stop and go back after a match, dont match children of a node
                                    return node_tracker
                        elif match_type == 1:
                            for att_value in self.attribute[attr].value:
                                if value in att_value:
                                    node_tracker.matches.append(self)
                                    #stop and go back after a match, dont match children of a node
                                    return node_tracker
            else:
                [node_tracker.matches.append(self) for attr in self.attribute if self.attribute[attr].name == attribute]
        node_tracker.node_count += 1
        for node in self.xml_node:
            if isinstance(element_number, int):
                if element_number > -1 and ((len(node_tracker.matches) - 1) == element_number):
                    return node_tracker
            node_tracker = node.get_element_attribute_node(node_tracker, attribute, value,element_number,match_type)
        return node_tracker

    #if data was read in from file, first element in node will be blank,might have data for content, if 
    #content wasnt a recognized elememnt ex:doctype declaration
    def display(self, std_out=1):
        node_tracker = NodeTracker()
        node_tracker.set_spacing(self.tab_spacing,self.element_line_spacing)
        self.display_text = self.map(node_tracker,1).display_text
        if std_out:
            sys.stdout.write(self.display_text)
        return self.display_text

    def show_attribute(self, attribute=""):
        attribute_combine = ""
        to_show = []
        if attribute:
            to_show.append(attribute)
        else:
            to_show.extend(self.sort_attribute())
            attribute_combine = " " 
        
        for attribute in to_show:
            attribute_combine += '='.join( (attribute,self.attribute[attribute].quote + " ".join(self.attribute[attribute].value) + self.attribute[attribute].quote))
            attribute_combine += ' '

        if attribute_combine:
            #remove last space from end
            return attribute_combine[:-1]
        else:
            return ''

    def set_map(self):
        node_tracker = NodeTracker()
        self.map(node_tracker)


    #this method is no longer needed in this class, disabled from in self.map()
    def set_map_row(self,node_tracker):
        self.node_map = []
        c = 0
        for row in range( self.node_count ,len(node_tracker.node_map)):
            if c:
                self.node_map.append([])

                if (len(node_tracker.node_map[row]) > len(node_tracker.node_map[row -1])):
                    child = 0
                elif (len(node_tracker.node_map[row]) == len(node_tracker.node_map[row -1])):
                    child = self.node_map[-2][-1] + 1
                elif (len(node_tracker.node_map[row]) < len(node_tracker.node_map[row -1])):
                    child = node_tracker.node_map[row-1][len( node_tracker.node_map[row]) -1] + 1

                for position in range(node_tracker.level ,len(node_tracker.node_map[row]) -1):
                    self.node_map[-1].append(node_tracker.node_map[row][position])

                self.node_map[-1].append(child)
            else:
                self.node_map.append([0])
            c += 1
    
    def map(self,node_tracker,display_state):
#        logfile.write('\n\n' + tab + 'level:' + str(node_tracker.level))
 #           logfile.write('\n' + tab + 'last:' + str(node_tracker.last))
  #          logfile.write('\n' + tab + 'content:' + self.content)  
   #         logfile.write('\n' + tab + 'element:' + self.element )
#           logfile.write('\n'+tab+'node_tracker.node_map:'+str(node_tracker.node_map))

#           logfile.write('\n'+tab+'count:'+str(count) )
 #           logfile.write('\n'+tab+'node_count:'+str(node_tracker.node_count) )

        tab_space = ' ' * (node_tracker.tab_spacing * node_tracker.level )
        element_line_space = '\n' * node_tracker.element_line_spacing

        if display_state and self.display_show and self.comment_value:
            node_tracker.display_text += element_line_space + tab_space + self.open + self.comment['open'] + self.comment_value + self.comment['close'] + self.close
#               logfile.write(element_line_space + tab_space + self.open + self.comment['open'] + self.comment_value + self.comment['close'] + self.close)

        if display_state and self.display_show and self.start_tag_present:
            if self.end_slash:
                end_bracet = '/' + self.close
            else:
                end_bracet = self.close
#               logfile.write(element_line_space + tab_space + self.open + self.element+self.show_attribute() + end_bracet + self.content)
            node_tracker.display_text += element_line_space + tab_space + self.open + self.element + self.show_attribute() + end_bracet + self.content

        self.node_count = node_tracker.node_count
        node_tracker.node_count += 1
        node_tracker.last = node_tracker.level
        node_tracker.level += 1

        for node in self.xml_node:
            node_tracker = node.map(node_tracker,display_state)

        if display_state and self.end_tag_present and self.display_show:
#               logfile.write(element_line_space + tab_space + self.end_open +self.element + self.close)
            node_tracker.display_text += (element_line_space + tab_space + self.end_open +self.element + self.close)

        if self.after_content:
            node_tracker.display_text += self.after_content
#               logfile.write(self.after_content)

        node_tracker.level -= 1
        return node_tracker
