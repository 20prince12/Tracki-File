import os
import shutil
import zipfile

def addToken(file,token):
    fin = open(os.path.join(file,'footer9999.xml'), 'rt')
    data = fin.read()
    txt = """pqrsxyzw"""
    data = data.replace(txt, token)
    fin.close()

    fout = open(os.path.join(file,'footer999.xml'), "wt")
    fout.write(data)
    fout.close()

    fin = open(os.path.join(file,'footer9999.xml.rels'), 'rt')
    data = fin.read()
    txt = """pqrsxyzw"""
    data = data.replace(txt, token)
    fin.close()

    fout = open(os.path.join(file,'footer999.xml.rels'), "wt")
    fout.write(data)
    fout.close()


def zipallFiles(source_file,destination):
    os.chdir(destination)
    shutil.make_archive("generated","zip",source_file)

def unzipFiles(source,destionation):
    with zipfile.ZipFile(source, "r") as zip_ref:
        zip_ref.extractall(destionation)

def gen_documentxmlrels(documentxmlrels):
    fin = open(documentxmlrels, 'rt', encoding="utf8")
    data = fin.read()
    txt = """<Relationship Id="rId999" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footer999.xml" />
</Relationships>"""
    data = data.replace('</Relationships>', txt)
    fin.close()
    fout = open(documentxmlrels, "wt", encoding="utf8")
    fout.write(data)
    fout.close()

def gen_contenttypesxml(contenttypesxml):
    fin = open(contenttypesxml, 'rt', encoding="utf8")
    data = fin.read()
    txt = """<Override PartName="/word/footer999.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml" />
</Types>"""
    data = data.replace('</Types>', txt)
    fin.close()
    fout = open(contenttypesxml, "wt", encoding="utf8")
    fout.write(data)
    fout.close()


def gen_documentxml(documentxml):
    fin = open(documentxml, 'rt', encoding="utf8")
    data = fin.read()
    txt = """<w:sectPr>
                <w:footerReference r:id="rId999" w:type="first" />
            </w:sectPr>
        </w:body>"""
    data = data.replace('</w:body>', txt)
    fin.close()
    fout = open(documentxml, "wt", encoding="utf8")
    fout.write(data)
    fout.close()


def wordgen(token,source_file):
    wordgenPath=os.getcwd()
    source_folder=os.path.join(wordgenPath,'source')
    destination_folder=wordgenPath


    unzipFiles(source_file,source_folder)

    #template paths
    templates=os.path.join(wordgenPath,'templates')
    addToken(templates,token)


    #copy templates
    shutil.copy(os.path.join(templates,'footer999.xml'),os.path.join(source_folder,'word'))
    shutil.copy(os.path.join(templates,'footer999.xml.rels'),os.path.join(source_folder,'word','_rels'))

    #modify xmls
    documentxmlrels=os.path.join(source_folder,'word','_rels','document.xml.rels')

    contenttypesxml=os.path.join(source_folder,'[Content_Types].xml')

    documentxml=os.path.join(source_folder,'word','document.xml')


    gen_documentxmlrels(documentxmlrels)

    gen_contenttypesxml(contenttypesxml)

    gen_documentxml(documentxml)


    zipallFiles(source_folder,destination_folder)
    #if os.path.exists(os.path.join(wordgenPath,'generated.docx')):
    #    os.remove(os.path.join(wordgenPath,'generated.docx'))

    shutil.rmtree(source_folder)

