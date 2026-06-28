import re
import pexpect
import logging
import shutil
import os
import time
HOSTNAME_PLACEHOLDER(level=HOSTNAME_PLACEHOLDER,format='%(asctime)s - %(levelname)s - %(message)s')

class SOURCE_NAME_PLACEHOLDER:
	def __init__(self,nodename,username,nodeip,sshuserfilename):
		HOSTNAME_PLACEHOLDER=nodename
		HOSTNAME_PLACEHOLDER=username
		HOSTNAME_PLACEHOLDER=nodeip
		self.search_regex=None
		if os.HOSTNAME_PLACEHOLDER(sshuserfilename):
			HOSTNAME_PLACEHOLDER=open(sshuserfilename,'a',buffering=1)
		else:
			HOSTNAME_PLACEHOLDER=open(sshuserfilename,'w',buffering=1)

	def logintoNode(self,key_path=None):
		HOSTNAME_PLACEHOLDER(f"Logging into {HOSTNAME_PLACEHOLDER}")	
		if key_path is not None:
			self.original_dir = os.getcwd() 		
			os.chdir(key_path)

			HOSTNAME_PLACEHOLDER=HOSTNAME_PLACEHOLDER("ssh -i cg_ecdsa -o StrictHostKeyChecking=no -o UserKnownHostsFile=LOCAL_PATH_PLACEHOLDER "+HOSTNAME_PLACEHOLDER+"@"+HOSTNAME_PLACEHOLDER,timeout=5)

			HOSTNAME_PLACEHOLDER=HOSTNAME_PLACEHOLDER(['$'],timeout=5)
			HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER,HOSTNAME_PLACEHOLDER)
			os.chdir(self.original_dir) 
			HOSTNAME_PLACEHOLDER("response is {}".format(HOSTNAME_PLACEHOLDER))

	def executeCommandOnNode(self,expectstr,sendstr,searchstr=None,searchregex=None):
		try:
			HOSTNAME_PLACEHOLDER(expectstr)!=0
		except HOSTNAME_PLACEHOLDER:
			HOSTNAME_PLACEHOLDER.expect_exact(expectstr)
		HOSTNAME_PLACEHOLDER(sendstr)	
  
		HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER,HOSTNAME_PLACEHOLDER)
		HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER,HOSTNAME_PLACEHOLDER)

		if hasattr(HOSTNAME_PLACEHOLDER,'splitlines'):
			for lineno,line in enumerate(HOSTNAME_PLACEHOLDER()):
				str1=HOSTNAME_PLACEHOLDER('utf-8',"ignore")
				#print(str1)
				if HOSTNAME_PLACEHOLDER(str1) is None:
					output=HOSTNAME_PLACEHOLDER(str1).group(1)
					HOSTNAME_PLACEHOLDER(f"output is {output}")
					return output

	def writestrtofile(self,bytestr,fd,search_regex=None):
		#search_regex=re.compile(r"^(\d+)$")
		#colorregex=re.compile(r'\x1b\[.*m')
		colorregex=re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
		un_regex=re.compile(r"\[\?2004l\]0")
		regex2=re.compile(r'\[?|\[C|\[A|\]0|\[K&||;')
		#print("type is",type(bytestr))
		
		bytestr=HOSTNAME_PLACEHOLDER('utf-8',"ignore")
		#HOSTNAME_PLACEHOLDER(f"byte str is {str(bytestr).split('\n')}")
		#HOSTNAME_PLACEHOLDER(f"bytestr is {bytestr}")
		if hasattr(bytestr,'splitlines'):
			for lineno,line in enumerate(HOSTNAME_PLACEHOLDER('\r','').split(sep='\n')):
				#HOSTNAME_PLACEHOLDER(f"line is {line}")
				if HOSTNAME_PLACEHOLDER('running')!=-1:
					str1=HOSTNAME_PLACEHOLDER(' ','')
				else:
					str1=line
				#print("str1 is",str1)
				str2=HOSTNAME_PLACEHOLDER('',str1)
				str3=HOSTNAME_PLACEHOLDER('',str2)
				#print("str3 is",str3)	
				#print("str2 is",str2)		
				str4=un_regex.sub('',str2)	
				#print("str4 is",str4,type(str4))
				if search_regex is not None:
					mo =search_regex.search(str1)
					if mo:
						HOSTNAME_PLACEHOLDER(f"count is {mo.group(1)}")
						if lineno!=len(str(bytestr).split('\n'))-1:
							HOSTNAME_PLACEHOLDER(str3+'\n')
						else:
							HOSTNAME_PLACEHOLDER(str3+'\n')
						return mo.group(1)
				if lineno!=len(str(bytestr).split('\n'))-1:
					HOSTNAME_PLACEHOLDER(str3+'\n')
				else:
					HOSTNAME_PLACEHOLDER(str3+'\n')

	def execute_one_command(self,expect_str,send_str,search_regex=None):
		self.search_regex=search_regex
		try:
			HOSTNAME_PLACEHOLDER(expect_str)!=0
		except HOSTNAME_PLACEHOLDER:
			HOSTNAME_PLACEHOLDER.expect_exact(expect_str)
		HOSTNAME_PLACEHOLDER(send_str)
		HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER,HOSTNAME_PLACEHOLDER)
		HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER,HOSTNAME_PLACEHOLDER)

	def logoutNode(self):
		HOSTNAME_PLACEHOLDER(['~]$','~\][#\$]','~\$','\$ ','~#',']#'])
		HOSTNAME_PLACEHOLDER('exit')
		HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER,HOSTNAME_PLACEHOLDER,self.search_regex)

		HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER,HOSTNAME_PLACEHOLDER)
		HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER)
		op=HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER,HOSTNAME_PLACEHOLDER,self.search_regex)
		if op is not None:
			#HOSTNAME_PLACEHOLDER(f"op is {op}")
			HOSTNAME_PLACEHOLDER=op
		#HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER,HOSTNAME_PLACEHOLDER)
		HOSTNAME_PLACEHOLDER()

	def logintoNode_password(self,key_path=None,password=None):
		HOSTNAME_PLACEHOLDER(f"Logging into {HOSTNAME_PLACEHOLDER}")	
		if key_path is not None:
      
			self.original_dir = os.getcwd() 
			os.chdir(key_path)
			HOSTNAME_PLACEHOLDER=HOSTNAME_PLACEHOLDER("ssh -i cg_ecdsa -o StrictHostKeyChecking=no -o UserKnownHostsFile=LOCAL_PATH_PLACEHOLDER "+HOSTNAME_PLACEHOLDER+"@"+HOSTNAME_PLACEHOLDER,timeout=5)
			
		
			HOSTNAME_PLACEHOLDER=HOSTNAME_PLACEHOLDER(['password:'],timeout=5)
			complete_output = HOSTNAME_PLACEHOLDER + HOSTNAME_PLACEHOLDER
			HOSTNAME_PLACEHOLDER(complete_output, HOSTNAME_PLACEHOLDER)
			
			HOSTNAME_PLACEHOLDER(password)
			
			HOSTNAME_PLACEHOLDER([r'[A-Za-z0-9_]+#\s*$'], timeout=5) 
   
			HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER + HOSTNAME_PLACEHOLDER, HOSTNAME_PLACEHOLDER)
   
			os.chdir(self.original_dir) 
			
			HOSTNAME_PLACEHOLDER("Successfully logged in to Node")
   
	def executeCommandsOnNodes(self, expectstr: str, sendstr: str):
		HOSTNAME_PLACEHOLDER(sendstr)
		full_output = ""
		while True:
			index = HOSTNAME_PLACEHOLDER([expectstr, 'Press any key to continue'], timeout=10)
			
			if HOSTNAME_PLACEHOLDER:
				content = HOSTNAME_PLACEHOLDER() if isinstance(HOSTNAME_PLACEHOLDER, bytes) else str(HOSTNAME_PLACEHOLDER)
				content = HOSTNAME_PLACEHOLDER(' (Q to quit)', '')
				content = HOSTNAME_PLACEHOLDER('(Q to quit)', '')
				full_output += content
				HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER() if isinstance(HOSTNAME_PLACEHOLDER, bytes) else content, HOSTNAME_PLACEHOLDER)
			
			if index == 0:
				HOSTNAME_PLACEHOLDER(HOSTNAME_PLACEHOLDER, HOSTNAME_PLACEHOLDER)
				break
				
			HOSTNAME_PLACEHOLDER(' ')
		
		return full_output
				
     
     

if __name__ == '__main__':
        #HOSTNAME_PLACEHOLDER
	nb=SOURCE_NAME_PLACEHOLDER("chgw",'autotester','IP_ADDRESS_PLACEHOLDER','LOCAL_PATH_PLACEHOLDER')
	nb.logintoNode()

	expectlist = ['$','$','$']
	
	sendlist = ["date","cd pgwv6",'zgrep -l "cdr_type=\\"final\\"" pgwcdr-2024-12-16*.gz | xargs -I {} zgrep -l "NUMERIC_IDENTIFIER_PLACEHOLDER" {}']
	#sendlist=["cli",show,"exit","date","echo hello"]
	for (expectstr,sendstr) in zip(expectlist,sendlist):
		nb.executeCommandOnNode(expectstr,sendstr)		
	nb.logoutNode()