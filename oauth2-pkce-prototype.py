#!/usr/bin/env python3
# vim: textwidth=0 wrapmargin=0 tabstop=2 shiftwidth=2 softtabstop smartindent

import os
import yaml
import logging
import argparse

import random, base64, hashlib
import json

###########################################################################
"""
 "  Configuration
"""
###########################################################################
__configfile_fd = os.open("fd-api-config.yaml", os.O_RDONLY)
__configfile = os.fdopen(__configfile_fd)
__config = yaml.load(__configfile, Loader=yaml.CLoader)
###########################################################################

###########################################################################
# Logging
###########################################################################
os.environ['TZ'] = 'UTC'
__default_loglevel = logging.INFO
__logger = logging.getLogger('fd-api')
__logger.setLevel(__default_loglevel)
__logger_ch = logging.StreamHandler()
__logger_ch.setLevel(__default_loglevel)
__logger_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s:\n%(message)s')
__logger_formatter.default_time_format = '%Y-%m-%d %H:%M:%S';
__logger_formatter.default_msec_format = '%s.%03d'
__logger_ch.setFormatter(__logger_formatter)
__logger.addHandler(__logger_ch)
###########################################################################

###########################################################################
# Command-Line Arguments
###########################################################################
__parser = argparse.ArgumentParser()
__parser.add_argument("--loglevel", help="set the log level to one of: DEBUG, INFO (default), WARNING, ERROR, CRITICAL")
__args = __parser.parse_args()
if __args.loglevel:
  __level = getattr(logging, __args.loglevel.upper())
  __logger.setLevel(__level)
  __logger_ch.setLevel(__level)
###########################################################################

###########################################################################
# MAIN
def main():
  __logger.debug('Start-Up')

  ########################################
  # Generate Code Verifier
  ########################################
  verifier = random.SystemRandom().getrandbits(8 * 32)
  __logger.debug('raw verifier: {}'.format(verifier))
  #verifier_b64 = base64.b64encode(verifier.to_bytes(32, byteorder='big'))
  verifier_b64 = base64.urlsafe_b64encode(verifier.to_bytes(32, byteorder='big'))
  __logger.debug('b64 verifier: {}'.format(verifier_b64))
  verifier_b64_str = verifier_b64.decode().replace('=','')
#.replace('+','-').replace('/','_').replace('=','')
  __logger.debug('str verifier: {}'.format(verifier_b64_str))
  ########################################

  ########################################
  # Generate Code Challenge
  ########################################
  challenge = hashlib.sha256(verifier_b64).digest()
  __logger.debug('raw challenge: {}'.format(challenge))
  challenge_b64 = base64.urlsafe_b64encode(challenge)
  __logger.debug('b64 challenge: {}'.format(challenge_b64))
  challenge_b64_str = challenge_b64.decode().replace('=','')
  __logger.debug('str challenge: {}'.format(challenge_b64_str))
  ########################################


  ########################################
  # Generate 'State'
  ########################################
  state = random.SystemRandom().getrandbits(8 * 32)
  __logger.debug('raw state: {}'.format(state))
  #state_b64 = base64.b64encode(state.to_bytes(32, byteorder='big'))
  state_b64 = base64.urlsafe_b64encode(state.to_bytes(32, byteorder='big'))
  __logger.debug('b64 state: {}'.format(state_b64))
  state_b64_str = state_b64.decode().replace('=','')
#.replace('+','-').replace('/','_').replace('=','')
  __logger.debug('str state: {}'.format(state_b64_str))
  ########################################


  ########################################
  # Store state and the codes for when redirect_uri is called
  ########################################
  auth_state = {
    'state': state_b64_str,
    'verifier': verifier_b64.decode(),
    'challenge': challenge_b64.decode()
  }
# XXX: Locking?
  authstate_fd = open("fd-api-authstate.json", mode="w")
  json.dump(auth_state, authstate_fd, indent=2)
  authstate_fd.close()
  ########################################

  ########################################
  # Get the User's Authorization
  ########################################
  __logger.debug("auth_api_url: '{}'".format(__config.get('auth_api_url')))
  request_uri = (__config.get('auth_api_url') +
      '/auth?audience=frontier'
      '&scope=auth'
      '&response_type=code'
      '&client_id=' + __config.get('clientid') +
      '&code_challenge=' + challenge_b64_str +
      '&code_challenge_method=S256'
      '&state=' + state_b64_str +
      '&redirect_uri=' + __config.get('redirect_uri')
  )
  print('Go to the following URL and Authorize the Application:\n\n{}\n'.format(request_uri))
  ########################################

if __name__ == '__main__':
      main()
