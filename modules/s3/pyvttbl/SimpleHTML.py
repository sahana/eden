#! /usr/bin/env python

# Roger Lew
# rogerlew@vandals.uidaho.edu
# (c) 2008 BSD

"""SimpleHTML Writer Module"""
import re
from copy import copy
from md5 import md5

def isfloat(string):
    """Returns True if string is a float"""
    try: float(string)
    except: return False
    return True

def md5sum(txt):
    return md5(txt).hexdigest()

def a(txt, href='', name='', target=''):
    if   href!='': return """\n\t\t\t<a href="%s" target="%s">%s</a>"""%(href, target, txt)
    elif name!='': return """\n\t\t\t<a name="%s">%s</a>"""%(name, txt)
    else         : return txt

def div(txt, id=''):
    return """\n\t\t\t<div id="%s">%s</div>"""%(id,txt)
    
def br(count=1):
    return """\n\t\t\t"""+"""<br/>"""*count

def h(txt, level=3, align='left'):
    return """\n\t\t\t<h%i align="%s">%s</h%i>"""%(level,align,txt,level)

def img(src, width=None, height=None, alt=''):
    rstr="""\n\t\t\t<img src="%s" alt="%s" """%(src,alt)
    
    if width!=None  : rstr+="""width=%i """%width
    if height!=None : rstr+="""height=%i """%height
    
    return rstr+"""/>"""

def pre(txt, align='left'):
    return """\n\t\t\t<pre align="%s">%s</pre>"""%(align,txt)

def p(txt, align='left'):
    return """\n\t\t\t<p align="%s">%s</p>"""%(align,txt)

def table(tbodys, thead=None, tfoot=None, border='1', cellpadding='8', rules='groups', frame='box'):
    s=[]
    s.append("""\n\t\t\t<table border=%s cellpadding=%s rules=%s frame=%s>"""%(border,cellpadding,rules,frame))
    if thead!=None:
        s.append("""\n\t\t\t\t<thead><tr>""")
        for x in thead:
            s.append("""<td>%s</td>"""%str(x))
        s.append("""</tr></thead>""")

    for tbody in tbodys:
        s.append("""\n\t\t\t\t<tbody>""")
        for x in tbody:                
            s.append("""\n\t\t\t\t\t<tr>""")
            for c in x:
                if isfloat(c) : s.append("""<td align='right'>%s</td>"""%str(c))
                else          : s.append("""<td>%s</td>"""%str(c))
            s.append("""</tr>""")
        s.append("""\n\t\t\t\t</tbody>""")
        
    if tfoot!=None:
        s.append("""\n\t\t\t\t<tfoot><tr>""")
        for x in tfoot:
            s.append("""<td>%s</td>"""%str(x))
        s.append("""</tr></tfoot>""")
            
    s.append("""\n\t\t\t</table>""")

    return ''.join(s)

def ul(depth_and_txt_list):
    """
    Wants a list of tuples containing depths and txt.
    Don't know how robust this function is to depth errors.
    
    depth_and_txt_list = [ (0, 'Things I want for x-mas'),
                           (1, 'Computer'),
                           (1, 'Fancy shoes'),
                           (0, 'New Years Resolutions'),
                           (1, 'Exercise more, program less'),
                           (1, 'Eat out less'),
                           (2, 'Except for Taco Time'),
                           (2, 'And Subway') ]
                           
    yields:

    <ul>
    <li>Things I want for x-mas
            <ul>
            <li>Computer</li>
            <li>Fancy shoes</li>
    </ul></li>
    <li>New Years Resolutions
            <ul>
            <li>Exercise more, program less</li>
            <li>Eat out less
                    <ul>

                    <li>Except for Taco Time</li>
                    <li>And Subway</li>
            </ul></li>
            </ul></li>
    </ul>

    """
    
    d = [depth_and_txt_list[0][0]]
    li=['\t'*d[-1]+'<ul>\n']
    
    for (req_d,txt) in depth_and_txt_list:
        if  req_d == d[-1]:
            li.append('\t'*d[-1]+'<li>%s'%txt)
            li.append('</li>\n')
            d.append(req_d)
            
        elif req_d > d[-1]:
            li.pop()
            li.append('\n'+'\t'*req_d+'<ul>\n')
            li.append('\t'*req_d+'<li>%s'%txt)
            li.append('</li>\n')
            d.append(req_d)
            
        elif req_d < d[-1]:
            li.append('\t'*req_d+'</ul></li>\n')
            li.append('\t'*req_d+'<li>%s'%txt)
            li.append('</li>\n')
            d.append(req_d)
            
            
    for i in range(d[-1]-d[0]):
            li.append('\t'*d[-1]+'</ul></li>\n')
            d.append(d[-1]-1)

    li.append('\t'*d[-1]+'</ul>\n')
    
    return ''.join(li)

class SimpleHTML:
    def __init__(self, title='', width='1000px', align='left', padding='1em', stylesheet=''):
        self.html=[]
        self.add("""\n<html>""")
        self.add("""\n\t<head>""")
                 
        if title!='':
            self.add("""<title>%s</title>"""%title)
        if stylesheet!='':
            self.add("""<link rel="stylesheet" type="text/css" href="%s"/>"""%stylesheet)

        self.add("""</head>""")
        
        if align=='center':
            self.add("""\n\t\t<body><div style="margin:0 auto; width:%s; padding:%s;">"""%(width,padding))
        else:
            self.add("""\n\t\t<body><div style="margin:0 0; width:%s; padding:%s;">"""%(width,padding))
            
        if title!='' : self.add(h(a(title,name='0_'+md5sum(title)),1,'center'))

    def add(self,txt):
        self.html.append(txt)

    def __str__(self):
        return ''.join(self.html)+"""\n\t</div></body>\n</html>"""
    
    def write(self, fname, opt=False):
        """Closes and writes html file"""

        txt2write=str(self)

        if opt:
            txt2write=txt2write.replace('\t','')
            txt2write=txt2write.replace('\n','')
            
        fid=open(fname,'wb')
        fid.write(txt2write)
        fid.close()

class NavFrame(SimpleHTML):
    def __init__(self, title='', default=0):
        SimpleHTML.__init__(self, width='500', padding='0em', stylesheet='nav.css')

        self.filelist=[]
        self.default=default
        self.pattern=pattern=r'<a name="(.*)">(.*)</a>'

    def addfile(self, fname):
        self.filelist.append(fname)
        
        dtxt=[] # list of (depths, hyperlinks)
        
        fid=open(fname,'r')
        matches=re.findall(self.pattern, fid.read())
        fid.close()

        for (href,txt) in matches:
            d=int(href[0])
            txt=txt.replace('Estimated Marginal Means for ','')
            txt=txt.replace('Summary Plot of ','')
            href='%s#%s'%(fname,href)
            dtxt.append((d, a(txt,href=href,target='showframe')))
            
        self.add(ul(dtxt))
        self.add(p(' '))

    def addfiles(self, filelist):
        for fname in filelist:
            self.addfile(fname)

    def getfilelist(self):
        return copy(self.filelist)
    
    def changedefault(self,index):
        self.default=index

    def getdefault(self,index):
        return copy(self.default)
        
    def build(self, fname='index.htm'):
            
        self.write('nav.htm')

        # nav stylesheet
        fid=open('nav.css','wb')
        fid.write('a { text-decoration:none; color:black; }\n')
        fid.write('a:hover { color:blue; }\n')
        fid.write('ul { list-style-type: none; padding:0; margin:0; }\n')
        fid.write('ul ul li a    { margin-left: 15px; }\n')
        fid.write('ul ul ul li a { margin-left: 30px; }\n')
        fid.close()

        # write index
        fid=open(fname,'wb')
        fid.write('<html>\n')
        fid.write('<frameset cols="200,*">\n')
        fid.write('<frame src="nav.htm">\n')
        fid.write('<frame src="%s" name="showframe">\n'%self.filelist[self.default])
        fid.write('</frameset>\n')
        fid.write('</html>\n')
        fid.close()

##html=SimpleHTML('Simple HTML Test')
##html.add(p('This is a python class to write html'))
##html.add(table([[[10,20,30],[40,50,60]],
##               [[70,80,90],[10,11,12]]],
##               thead=['A','B','C']))
##html.add(img('that.png',width=1000))
##
##print ''.join(html.html)
## 
##html.write('simpleHTML.htm')
