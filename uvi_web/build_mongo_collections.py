import json
import os
from pprint import pprint
import nltk
from lxml import etree
import re

path_framenet = '../corpora/framenet/'
path_propbank = '../corpora/propbank/frames/'
path_verbnet = '../corpora/verbnet/'
path_wordnet = '../corpora/wordnet/'

from pymongo import MongoClient

mongo_client = MongoClient()
db = mongo_client['uvi_corpora']


#VERBNET
def build_verbnet_collection():
	print('Building VN Collection...')
	#VERBNET
	import spacy
	from spacy import displacy
	spacy_nlp = spacy.load('en')

	def parse_member(member):
		name = member.get('name')
		wn = member.get('wn').split(' ')
		grouping = member.get('grouping').split(' ')
		vs_features = member.get('features')
		if vs_features != None:
			vs_features = vs_features.split(' ')
		if wn[0] == '':
			wn = None
		if grouping[0] == '':
			grouping = None

		return {'name': name, 'wn': wn, 'grouping': grouping, 'vs_features': vs_features}
			
	def parse_themrole(themrole):
		def parse_selrestr(selrestr):
			selrestr_type = selrestr.get('type')
			value = selrestr.get('Value')
			return {'value': value, 'type': selrestr_type}
		
		def parse_synrestr(synrestr):
			synrestr_type = synrestr.get('type')
			value = synrestr.get('Value')
			return {'value': value, 'type': synrestr_type}
			
		themrole_type = themrole.get('type')
		
	#     selrestr_logic = themrole.find('SELRESTRS').get('logic')
		
	#     if selrestr_logic == None: selrestr_logic = 'and'
	#     if selrestr_logic.strip() == 'and': selrestr_logic = '&'
	#     elif selrestr_logic.strip() == 'or': selrestr_logic = '|'
			
	#     selrestrs = [parse_selrestr(selrestr) for selrestr in themrole.find('SELRESTRS')]
		found_selrestrs = themrole.find('SELRESTRS')
		if found_selrestrs is not None: 
			if found_selrestrs.get('logic'):
				selrestr_logic = found_selrestrs.get('logic')
			else:
				selrestr_logic = 'and'

			if selrestr_logic.strip() == 'and': selrestr_logic = '&'
			elif selrestr_logic.strip() == 'or': selrestr_logic = '|'

			if len(found_selrestrs) > 0: 
				selrestrs = [parse_selrestr(selrestr) for selrestr in found_selrestrs]
			else:
				selrestrs = None
		else:
			selrestrs = None
			selrestr_logic = None

		found_synrestrs = themrole.find('SYNRESTRS')
		if found_synrestrs is not None:
			if found_synrestrs.get('logic'):
				synrestr_logic = found_synrestrs.get('logic')
			else:
				synrestr_logic = 'and'

			if synrestr_logic.strip() == 'and': synrestr_logic = '&'
			elif synrestr_logic.strip() == 'or': synrestr_logic = '|'

			synrestrs = [parse_synrestr(synrestr) for synrestr in found_synrestrs]
			
		else:
			synrestrs = None
			synrestr_logic = None
		
		return {'themrole': themrole_type, 'selrestrs': {'selrestrs_list':selrestrs, 'selrestr_logic':selrestr_logic}, 'synrestrs': {'synrestr_list': synrestrs, 'synrestr_logic':synrestr_logic}}

	def parse_frame(frame):
		def parse_description(frame_description):
			primary = frame_description.get('primary')
			secondary = frame_description.get('secondary')
			number = frame_description.get('descriptionNumber')
			xtag = frame_description.get('xtag')
			return {'primary': primary, 'secondary': secondary, 'number': number, 'xtag': xtag}
		
		def parse_syntax_arg(syntax_arg):
			def parse_selrestr(selrestr):
				if selrestr.tag == 'SELRESTRS':
					return [parse_selrestr(selrestr) for selrestr in found_selrestrs]
				selrestr_type = selrestr.get('type')
				value = selrestr.get('Value')
				return {'value': value, 'type': selrestr_type}
			
			def parse_synrestr(synrestr):
				synrestr_type = synrestr.get('type')
				value = synrestr.get('Value')
				return {'value': value, 'type': synrestr_type}
			
			arg_type = syntax_arg.tag
			if arg_type == 'VERB': value = 'VERB'
			elif arg_type == 'PREP':
				value = syntax_arg.get('value')
				#if no values specified (e.g. attend-107.4-1), return generic placeholder string 'PREP'
				if value == None: value = 'PREP'
				#resolves inconsistencies in how the prep values are saved in the XML
				else: value = value.replace('| ', '')

			else: value = syntax_arg.get('value')
				
			found_selrestrs = syntax_arg.find('SELRESTRS')
			if found_selrestrs is not None: 
				if found_selrestrs.get('logic'):
					selrestr_logic = found_selrestrs.get('logic')
				else:
					selrestr_logic = 'and'
				
				if selrestr_logic.strip() == 'and': selrestr_logic = '&'
				elif selrestr_logic.strip() == 'or': selrestr_logic = '|'
					
				if len(found_selrestrs) > 0: 
					selrestrs = [parse_selrestr(selrestr) for selrestr in found_selrestrs]
				else:
					selrestrs = None
			else:
				selrestrs = None
				selrestr_logic = None
			
			found_synrestrs = syntax_arg.find('SYNRESTRS')
			if found_synrestrs is not None:
				if found_synrestrs.get('logic'):
					synrestr_logic = found_synrestrs.get('logic')
				else:
					synrestr_logic = 'and'
				
				if synrestr_logic.strip() == 'and': synrestr_logic = '&'
				elif synrestr_logic.strip() == 'or': synrestr_logic = '|'
					
				if len(found_synrestrs) > 0: 
					synrestrs = [parse_synrestr(synrestr) for synrestr in found_synrestrs]
				else:
					synrestrs = None
			else:
				synrestrs = None
				synrestr_logic = None
				
			return {'arg_type': arg_type, 'value': value, 'selrestrs': {'selrestr_list': selrestrs, 'selrestr_logic': selrestr_logic }, 'synrestrs': {'synrestr_list': synrestrs, 'synrestr_logic':synrestr_logic}}
		
		def parse_pred(predicate):
			def parse_arg(arg):
				arg_type = arg.get('type')
				value = arg.get('value')
				return {'arg_type': arg_type, 'value': value}
				
			pred_value = predicate.get('value')
			boolean = predicate.get('bool')

			args = [parse_arg(arg) for arg in predicate.find('ARGS')]
			return {'predicate': pred_value, 'args': args, 'bool': boolean}
		
		def dependency_tree_svg(example_text):
			spacy_doc = spacy_nlp(example_text)
			return displacy.render(spacy_doc,style='dep', options={'compact':True})
		
		description = parse_description(frame.find('DESCRIPTION'))
		examples = [{'example_text':example.text, 'svg': dependency_tree_svg(example.text)} for example in frame.find('EXAMPLES')]
		syntax = [parse_syntax_arg(arg) for arg in frame.find('SYNTAX')]
		semantics = [parse_pred(pred) for pred in frame.find('SEMANTICS')]
		return {'description': description, 'examples': examples, 'syntax': syntax, 'semantics': semantics}

	def parse_numerical_comparison_id(class_id):
		num_format_list = ''.join(class_id.split('-')[1:]).split('.')
		return float(num_format_list[0]+'.'+''.join(num_format_list[1:]))

	def parse_vn_class(vn_class):
		class_id = vn_class.get('ID')
		num_comparison_id = parse_numerical_comparison_id(class_id)
		members = [parse_member(member) for member in vn_class.find('MEMBERS') if member.tag == 'MEMBER']
		themroles = [parse_themrole(themrole) for themrole in vn_class.find('THEMROLES') if themrole.tag == 'THEMROLE']
		frames = [parse_frame(frame) for frame in vn_class.find('FRAMES') if frame.tag == 'FRAME']
		subclasses = [parse_vn_class(subclass) for subclass in vn_class.find('SUBCLASSES') if subclass.tag=='VNSUBCLASS']
		if not subclasses:
			subclasses = None
		return {'class_id': class_id, 'num_comparison_id': num_comparison_id, 'members': members, 'themroles': themroles, 'frames': frames, 'subclasses': subclasses, 'resource_type': 'vn'}

	def include_subclasses(vn_classes):
		for vn_class in vn_classes:
			subclasses = vn_class['subclasses']
			if subclasses:
				vn_classes.extend(subclasses)
		return vn_classes



	#Populate the database
	def vn_to_mongo(file):
		with open(path_verbnet+file,'r') as xml_file:
			root = etree.parse(xml_file).getroot()
			vn_class = parse_vn_class(root)
			return vn_class

	verbnet_xml = [f for f in os.listdir(path_verbnet) if f.endswith('.xml')]
	verbnet_mongo = include_subclasses([vn_to_mongo(f) for f in verbnet_xml])

	db.drop_collection('verbnet')
	vn_collection = db['verbnet']
	vn_collection.insert_many(verbnet_mongo)



	#VN Reference Information (themrole defs, predicate defs, etc.)
	predicate_definition_files = ['reference_docs/'+f for f in ['vn_verb_specific_predicates.tsv',
	 'vn_semantic_predicates.tsv',
	 'vn_constants.tsv']]

	def add_predicate_defs(predicate_definition_file, mongo_collection):
	    with open(predicate_definition_file, 'r') as definition_tsv:
	        #skip first line (tsv heading)
	        next(definition_tsv)
	        for line in definition_tsv:
	            pred_fields = line.split('\t')
	            pred_name = pred_fields[0].split('(')[0].strip()
	            pred_def = pred_fields[1]
	            pred_args = pred_fields[2]
	            pred_dict = {'name':pred_name, 'def':pred_def, 'args':pred_args}
	            mongo_collection.insert_one(pred_dict)

	db.drop_collection('vn_predicates')
	vn_pred_collection = db['vn_predicates']
	add_predicate_defs('reference_docs/vn_semantic_predicates.tsv', vn_pred_collection)

	db.drop_collection('vn_constants')
	vn_constant_collection = db['vn_constants']
	add_predicate_defs('reference_docs/vn_constants.tsv', vn_constant_collection)

	db.drop_collection('vn_verb_specific')
	vn_verb_specific_collection = db['vn_verb_specific']
	add_predicate_defs('reference_docs/vn_verb_specific_predicates.tsv', vn_verb_specific_collection)


	html_dir = 'reference_docs/vn_themrole_html/'
	html_files = [html_dir + f for f in os.listdir(html_dir)]

	themrole_defs = []

	for html_file in html_files:
	    html_doc = open(html_file,'r')
	    soup = BeautifulSoup(html_doc, 'html.parser')
	    h3_tags = [t.get_text() for t in soup.find_all('h3')]
	    
	    themrole = str(soup.h2).split(':')[1].split('<')[0].strip()
	    description = 'No description found'
	    example = 'No examples found'
	    
	    for tag in h3_tags:
	        tag_fields = tag.split(':')
	        if tag_fields[0].strip() == 'Description':
	            description = tag_fields[1].strip()
	        elif tag_fields[0].strip() == 'Example':
	            example = tag_fields[1].strip()
	    
	    themrole_dict = {'name':themrole, 'description':description, 'example':example}
	    themrole_defs.append(themrole_dict)

	db.drop_collection('vn_themroles')
	vn_themroles_db = db['vn_themroles']
	vn_themroles_db.insert_many(themrole_defs)


	def get_themrole_fields(class_id, frame_json, themrole_name):
	    #Get Class ID's for parent classes of current class (returned list includes the original class)
	    themrole_name_stripped = themrole_name.strip('?').strip('_i').strip('_j').strip('Co-')
	    
	    #Edge case: Co-Patient not defined; use attributes for Patient
	#     if themrole_name_stripped == 'Co-Patient': 
	#         themrole_name_stripped = 'Patient'

	    selrestr_list = None
	    selrestr_logic = None
	    
	    #Get the list of parent class id's (up to & including current class_id) from which this class would inherit semantic restrictions (if any)
	    parents = [('-').join(class_id.split('-')[:x]) for x in range(2, len(class_id.split('-'))+1)]
	    for parent_class_id in parents:
	        selrestr_fields = db['verbnet'].find_one({ 'class_id': parent_class_id, 'themroles.themrole':themrole_name_stripped}, {'themroles.themrole.$':1})
	        if selrestr_fields:
	            selrestr_list = selrestr_fields['themroles'][0]['selrestrs']['selrestrs_list']
	            selrestr_logic = selrestr_fields['themroles'][0]['selrestrs']['selrestr_logic']
	    
	    themrole_entry = db['vn_themroles'].find_one({'name':themrole_name_stripped})

	    if themrole_entry:
	        themrole_desc = themrole_entry['description']
	        themrole_example = themrole_entry['example']
	    else:
	        themrole_desc = 'no entry found'
	        themrole_example = 'no entry found'
	        
	    frame_syntax = frame_json['syntax']
	    synrestrs = [arg['synrestrs'] for arg in frame_syntax if arg['value'] == themrole_name_stripped]
	    if synrestrs == []:
	        synrestr_list = None
	        synrestr_logic = None
	    else:
	        synrestr_list = synrestrs[0]['synrestr_list']
	        synrestr_logic = synrestrs[0]['synrestr_logic']
	    
	    frame_level_selrestrs = [arg['selrestrs'] for arg in frame_syntax if arg['value'] == themrole_name_stripped]
	    if frame_level_selrestrs == []:
	        frame_level_selrestr_list = None
	        frame_level_selrestr_logic = None
	    else:
	        frame_level_selrestr_list = frame_level_selrestrs[0]['selrestr_list']
	        frame_level_selrestr_logic = frame_level_selrestrs[0]['selrestr_logic']

	    return {'selrestr_list':selrestr_list, 'selrestr_logic':selrestr_logic, 'synrestr_list':synrestr_list, 
	    'synrestr_logic':synrestr_logic, 'themrole_desc':themrole_desc, 'themrole_example':themrole_example,
	    'frame_level_selrestrs_list':frame_level_selrestr_list, 'frame_level_selrestrs_logic': frame_level_selrestr_logic}

	def aggregate_themrole_list(class_id):
	    parents = [('-').join(class_id.split('-')[:x]) for x in range(2, len(class_id.split('-'))+1)]
	    themroles = []
	    for parent_class_id in parents:
	        parent_themroles = [themrole['themrole'] for themrole in db['verbnet'].find_one({'class_id': parent_class_id}, {'themroles.themrole':1})['themroles']]
	        themroles.extend(parent_themroles)
	    return list(set(themroles))

	db.drop_collection('vn_themrole_fields')
	vn_themrole_fields = db['vn_themrole_fields']

	vn_class_ids = [class_id['class_id'] for class_id in list(db.verbnet.find({},{'class_id':1, '_id':0}))]
	for class_id in vn_class_ids:
	    class_frames = db.verbnet.find_one({'class_id':class_id}, {'frames.examples.svg':0})['frames']
	    class_themrole_names = aggregate_themrole_list(class_id)
	    for frame_json in class_frames:
	        frame_desc = frame_json['description']['primary']
	        for themrole_name in class_themrole_names:
	            themrole_fields = get_themrole_fields(class_id, frame_json, themrole_name)
	            vn_themrole_fields.insert_one({'class_id': class_id, 'frame_desc': frame_desc, 'themrole_name': themrole_name, 'themrole_fields': themrole_fields})



#FRAMENET
def parse_fn_def(definition_markup):
    def_split = definition_markup.split('<ex>')
    def_text_markup = def_split[0].strip()
    examples_markup = [ex.replace('<ex>','').replace('</ex>','').strip() for ex in def_split[1:]]
    return {'def_text_markup': def_text_markup, 'examples_markup': examples_markup}
    
def parse_frame_element(frame_element):
    def_markup = frame_element['definitionMarkup'].replace('<def-root>','').replace('</def-root>','').strip()
    return {'fe_name': frame_element['name'], 'core_type': frame_element['coreType'], 'abbrev': frame_element['abbrev'], 'def_markup': def_markup}

def parse_lexical_unit(lexical_unit):
    lu_name = ('_').join(lexical_unit['name'].split(' '))
    return {'lu_name': lu_name, 'lu_def': lexical_unit['definition'], 'url': lexical_unit['URL']}

from nltk.corpus.reader.framenet import FramenetCorpusReader

def fn_to_mongo(frame):
    frame_definition = parse_fn_def(frame['definitionMarkup'])
    frame_elements = [parse_frame_element(frame['FE'][fe]) for fe in frame['FE'].keys()]
    lexical_units = [parse_lexical_unit(frame['lexUnit'][lu]) for lu in frame['lexUnit'].keys()]
    fn_frame = {'name': frame['name'], 'definition': frame_definition, 'elements': frame_elements, 'lexical_units': lexical_units, 'url': frame['URL'], 'resource_type': 'fn'}
    return fn_frame

fn = FramenetCorpusReader(path_framenet, [f for f in path_framenet if f.endswith('.xml')])
frames = fn.frames()
framenet_mongo = [fn_to_mongo(f) for f in frames]

db.drop_collection('framenet')
fn_collection = db['framenet']
fn_collection.insert_many(framenet_mongo)


#PROPBANK
def parse_predicate(predicate):
    def parse_roleset(roleset):
        def parse_aliases(aliases):
            alias_list = []
            for alias in aliases:
                alias_name = alias.text
                pos = alias.get('pos')
                fn = alias.get('framenet').split(' ') if alias.get('framenet') else ''
                vn = alias.get('verbnet').split(' ') if alias.get('verbnet') else ''
                alias_list.append({'alias_name': alias_name, 'pos': pos, 'fn': fn, 'vn': vn})
            return alias_list
        
        def parse_roles(roles):
            role_list = []
            for role in roles:
                descr = role.get('descr')
                f = role.get('f')
                n = role.get('n')
                
                vnroles_found = role.findall('vnrole')
                if vnroles_found:
                    vnroles = [vnrole.get('vncls')+'-'+vnrole.get('vntheta').lower() for vnrole in vnroles_found]
                    
                else:
                    vnroles = None
                role_list.append({'descr':descr, 'f': f, 'n': n, 'vnroles': vnroles})
            return role_list
        
        def parse_examples(examples):
            def parse_ex_args(args):
                args_list = []
                for arg in args:
                    arg_text = arg.text
                    f = arg.get('f')
                    n = arg.get('n')
                    args_list.append({'arg_text': arg_text, 'f':f, 'n':n})
                return args_list
            
            def parse_ex_rel(rel):
                if rel != None:
                    rel_text = rel.text
                    f = rel.get('f')
                else:
                    rel_text = ''
                    f = ''
                return {'rel_text': rel_text, 'f': f}

            example_list = []
            for example in examples:
                example_name = example.get('name')
                example_text = example.find('text').text
                args = parse_ex_args(example.findall('arg'))
                rel = parse_ex_rel(example.find('rel'))
                
                
                example_list.append({'example_name': example_name, 'example_text': example_text, 'args': args, 'rel': rel})
            
            return example_list
                    
        roleset_id = roleset.get('id')
        roleset_name = roleset.get('name')
        aliases = parse_aliases(roleset.find('aliases'))
        roles = parse_roles(roleset.find('roles'))
        examples = parse_examples(roleset.findall('example'))
        
        return {'roleset_id': roleset_id, 'roleset_name': roleset_name, 'aliases': aliases, 'roles': roles, 'examples': examples}

    lemma = predicate.get('lemma')
    rolesets = [parse_roleset(r) for r in predicate.findall('roleset')]
    
    return {'lemma': lemma, 'rolesets': rolesets}

def parse_pb_frame(pb_frame):
    predicates = [parse_predicate(p) for p in pb_frame.findall('predicate')]
    return {'predicates':predicates, 'resource_type': 'pb'}

def pb_to_mongo(file):
    with open(path_propbank+file,'r') as xml_file:
        root = etree.parse(xml_file).getroot()
        pb_frame = parse_pb_frame(root)
        pb_frame['frameset_id'] = file[:-4]
        return pb_frame
    
propbank_xml = [f for f in os.listdir(path_propbank) if f.endswith('.xml')]
propbank_mongo = [pb_to_mongo(f) for f in propbank_xml]

db.drop_collection('propbank')
pb_collection = db['propbank']
pb_collection.insert_many(propbank_mongo)