# -*- encoding: utf-8 -*-
#
#  wkhtmltopdfpy
#
#  Created by Pascal Bach
#  Some code is taken from c2c_webkit_report
#
#  Copyright (c) 2010 Pascal Bach. All rights reserved.
##############################################################################
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import subprocess
import tempfile
import platform
import os

from urlparse import urlparse

class WebkitHTMLError(Exception):
    """ General Error in WebkitHTML 
    
        All other errors are subclasses of this error
    """

class UnsupportedSystemError(WebkitHTMLError):
    """ The system is not supported by the built-in static binaries of wkhtmltopdf 
    
        You can provide a binary to the constructor of WebkitHTML yourself
    """
    
class MissingLibraryError(WebkitHTMLError):
    """ The binary of wkhtmltopdf could not be located """

class WebkitHTML(object):
    """ 
    Python wrapper around wkhtmltopdf.
    
    It has built-in static compiled versions of wkhtmltopdf 
    for Linux, Windows and Max OS X.
    
    You can specify your own binary to be used instead using the
    ``binary`` argument of the constructor.
    
    """
    def __init__(self, binary=None):
        """
        The ``binary``argument allows to specify a binary of ``wkhtmltopdf``
        to be used instead of the build in variants.
        """

        self.binary = binary
    
    def get_lib(self) :
        """
        Return the path of the wkhtmltopdf binary.
        """
        #TODO Detect system binary first
        
        # If no binary is provided try to find a built-in one
        if not self.binary:
            curr_sys = platform.system()
            sysmapping = {
                        'Linux': 'wkhtmltopdf-linux-i386-0-9-9',
                        'Darwin': 'wkhtmltopdf-0.9.9-OS-X.i368',
                        'Windows' : os.path.join('wkhtmltopdf', 'wkhtmltopdf.exe')
                            
                         }
            if not curr_sys in sysmapping.keys() :
                raise UnsupportedSystemError(u'''Your system (%s) is not yet supported. 
                    Currently supported systems are: %s''' % (curr_sys, ", ".join(sysmapping.keys()) )) 
            
            import liblocator
            path = os.path.join(    liblocator.path(),
                                    'lib', 
                                    sysmapping[curr_sys])
                                
        else:
            path = self.binary
            
        if not os.path.exists(path) :
            raise MissingLibraryError(u'Can not find wkhtmltopdf binary at location "%s".' %(path) )
            
        return path
        
        
    def render(self, output_file, content, header=None, footer=None, subst={}, args=[]):
        """ 
        Renders the content to ``output_file``.
        
        ``output_file`` should be a filename where the pdf should be saved.
        If ``output_file`` is set to ``None``then the output is returned as
        a byte ``str``.
        
        ``content`` can eighter be a ``list`` of strings, filenames, and urls.
        WebkitHTML will try to figure out the type handle it accordingly.
        
        ``header`` and ``footer` can each eigher be a string, filename or url.
        WebkitHTML will try to figure out the type handle it accordingly. If 
        set to ``None`` they will be omitted in the final report.
        
        ``subst`` is a ``dict`` of values that are send to wkhtmltopdf by setting
        a cookie. They can be accesses via JavaScript in your HTML files.
        
        ``args`` is a ``list`` of addtional argument that you want to specify to
        wkhtmltopddf. See wkhtmltopdf --help for more information.
        """
        header_file = footer_file = output_file_temp = None
        content_files = []
        
        output = ""
        
        arguments = []
        arguments.append(self.get_lib())
        arguments.extend(args)
        
        for name, value in subst.items():
            arguments.append("--cookie")
            arguments.append(name)
            arguments.append(value)
            
        
        if header:
            url = urlparse(header)
            if url.scheme:
                # Header is an url, append it as is
                arguments.append("--header-html")
                arguments.append(header)
            elif os.path.isfile(header.encode("utf8")):
                # Header is a file, append it as is, we use utf8 filenames
                arguments.append("--header-html")
                arguments.append(header.encode("utf8"))
            else:
                # Header is a string, write it to a temporary file and use this file as input
                header_file = tempfile.NamedTemporaryFile(mode='w+', prefix="header_", suffix=".html")
                header_file.write(header.encode("utf8"))
                header_file.flush()
                arguments.append("--header-html")
                arguments.append(header_file.name)
            
        if footer:
            url = urlparse(footer)
            if url.scheme:
                # Footer is an url, append it as is
                arguments.append("--footer-html")
                arguments.append(footer)
            elif os.path.isfile(footer.encode("utf8")):
                # Footer is a file, append it as is, we use utf8 filenames
                arguments.append("--footer-html")
                arguments.append(footer.encode("utf8"))
            else:
                # Footer is a string, write it to a temporary file and use this file as input
                footer_file = tempfile.NamedTemporaryFile(mode='w+', prefix="footer_", suffix=".html")
                footer_file.write(footer.encode("utf8"))
                footer_file.flush()
                arguments.append("--footer-html")
                arguments.append(footer_file.name)
        
        if isinstance(content, basestring):
            content = [content]
        
        for content_item in content:
            url = urlparse(content_item)
            if url.scheme:
                arguments.append(content_item)
            elif os.path.isfile(content_item):
                arguments.append(content_item)
            else:
                content_file = tempfile.NamedTemporaryFile(mode='w+', prefix="content_", suffix=".html")
                content_file.write(content_item.encode("utf8"))
                content_file.flush()
                content_files.append(content_file)
                arguments.append(content_file.name)
        
        if not output_file:
            output_file_temp = tempfile.NamedTemporaryFile(mode='wb', prefix="output_", suffix=".pdf", delete=False)
            output_file_temp.close()
            output_file = output_file_temp.name
        
        arguments.append(output_file)
        
        print arguments
        
        subprocess.call(arguments)
        
        if output_file_temp:
            output_file_temp = open(output_file_temp.name, "rb")
            output = output_file_temp.read()
            output_file_temp.close()
            os.remove(output_file_temp.name)
            
        
        for content_file in content_files:
            content_file.close()
        if header_file: header_file.close()
        if footer_file: footer_file.close()
        
        return output


        
if __name__ == "__main__":
    wk = WebkitHTML()
    
    config = ["--margin-bottom", "2.5cm",
              "--margin-top", "2.5cm",]

    subst = {"offset":"Hallo2"}
    
    content = ["body.html",]
               
    wk.render("test.pdf",     content=content, 
                            header="header.html", 
                            footer="footer.html", 
                            subst=subst,
                            args=config)    