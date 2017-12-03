import os
import glob
import zipfile
from collections import defaultdict, OrderedDict
from lxml import etree
import xmltodict
import pdb;
import traceback
import pprint
from navigator import Navigator
NAMESPACES =  {
    'n':'urn:oasis:names:tc:opendocument:xmlns:container',
    'pkg':'http://www.idpf.org/2007/opf',
    'dc':'http://purl.org/dc/elements/1.1/'
}
  

class InvalidEPub(zipfile.BadZipfile):
    pass

class Books150(object):
      
    def __init__(self, ebook=None):
        self.ebook = ebook
        self.ns = NAMESPACES
        self.opf = None
        self.package = None
        self.metadata = defaultdict(dict)
        self.manifest = defaultdict(dict)
        self.root = None
        
    def __enter__(self):
        self.open(self.ebook)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            print (exc_value)
            pdb.set_trace()
            pass
            # return False # uncomment to pass exception through
        return self.close()

    def open(self, ebook=None):
        if ebook:
            self.ebook = ebook
        print("\n Reading: ", os.path.basename(self.ebook))
        if self.ebook and not os.path.exists(self.ebook):
            raise FileNotFoundError()
        try:
            # prepare to read from the .epub file
            self.ebook = zipfile.ZipFile(self.ebook)
        except Exception as e:
            print(traceback.format_exc())

    def close(self):
        try:
            self.ebook.close()
        except AttributeError: # obj isn't closable
            print ('Not closable.')
        return True # exception handled successfully
        
    def read_from_epub(self, file_from_epub):
        txt = str(self.ebook.read(file_from_epub).decode('utf8'))
        return txt

    def locate_opf(self):
        try:
            # find the contents of metafile
            txt = self.read_from_epub('META-INF/container.xml')
            utf8_parser = etree.XMLParser(ns_clean=True, recover=True,
                                          encoding='utf-8',
                                          remove_blank_text=True)
            tree = etree.fromstring(txt.encode('utf-8'),
                                    parser=utf8_parser)
            rootopf = tree.xpath('n:rootfiles/n:rootfile/@full-path',
                              namespaces=self.ns)[0]
            self.root, opf = os.path.split(rootopf)
            return rootopf
        except Exception as e:
            print(traceback.format_exc())

    def load_opf(self, opfpath=None):
        opfxml = self.read_from_epub(opfpath)
        self.opf = xmltodict.parse(opfxml)
        self.load_package()
        self.ns = {key: value for key, value in self.package.items()
               if key.startswith('@')}   
        self.load_metadata()
        self.load_manifest()
        self.load_spine()
        
    def load_package(self):
        self.package = (self.opf.get('package') or
                        self.opf.get('opf:package')) 

    def load_metadata(self):
        metadata = (self.package.get('metadata') or
                     self.package.get('opf:metadata'))
        meta = defaultdict(dict)
        for metakey, val in metadata.items():
            if isinstance(val, OrderedDict):
                meta[metakey] = val.get("#text")
            else:
                meta[metakey] = val
        return meta

    def load_manifest(self):
        manifest = (self.package.get('manifest') or
                    self.package.get('opf:manifest'))
        _items = manifest.get('item') or manifest.get('opf:item') 
        for i in _items:
            self.manifest.update({i.get('@id'): i})

    def load_spine(self):
        spine = (self.package.get('spine') or
                 self.package.get('opf:spine'))
        
        for key, pageinfo in spine.items():
            if key.strip().lower() in ['itemref', 'opf:itemref']:
                if isinstance(pageinfo, OrderedDict):
                    idref = pageinfo.get('@idref')
                    yield idref, self.manifest.get(idref)
                if isinstance(pageinfo, list):
                    for pageref in pageinfo:
                        idref = pageref.get('@idref')
                        yield idref, self.manifest.get(idref)

    def pages(self):
        for page_id, pageinfo in self.load_spine():
            page = os.path.join(self.root, pageinfo.get('@href'))
            yield page_id, self.read_from_epub(page) 
    
        
if __name__ == '__main__':
    try:
        path = "/home/sofycomps/work/"
        epubs = os.path.join(path, 'input', '*.epub')
        epubs_dir = glob.glob(epubs)
        for epubfile in epubs_dir:
            with Books150(epubfile) as eReader:
                opfpath = eReader.locate_opf()
                eReader.load_opf(opfpath)
                pages = eReader.pages()
                nav = Navigator(pages)
                pdb.set_trace()
    except Exception as e:
        print(traceback.format_exc())