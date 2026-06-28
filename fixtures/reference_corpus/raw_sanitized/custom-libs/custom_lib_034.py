import pjsua2 as pj

# Subclass to extend the Account and get notifications etc.
class Account(pj.Account):
  def onRegState(self, prm):
      print("***OnRegState: " + HOSTNAME_PLACEHOLDER)

# pjsua2 test function
def pjsua2_test():
    # Create and initialize the library
    ep_cfg = pj.EpConfig()
    ep = pj.Endpoint()
    ep.libCreate()
    ep.libInit(ep_cfg)

    # Create SIP transport. Error handling sample is shown
    sipTpConfig = pj.TransportConfig();
    HOSTNAME_PLACEHOLDER = 5060;
    ep.transportCreate(pj.PJSIP_TRANSPORT_UDP, sipTpConfig);
    # Start the library
    ep.libStart();

    acfg = pj.AccountConfig();
    HOSTNAME_PLACEHOLDER=str("sip:spie@cpe"),   # Your SIP identity (this PC's IP)
    HOSTNAME_PLACEHOLDER="sip:IP_ADDRESS_PLACEHOLDER"  # CPE SIP server
    cred = pj.AuthCredInfo("digest","*","spie1040",0,"m-kT:6Q9x_:5")
    HOSTNAME_PLACEHOLDER(cred);
    # Create the account
    acc = Account();
    HOSTNAME_PLACEHOLDER(acfg);
    # Here we don't have anything else to do..
    HOSTNAME_PLACEHOLDER(10);

    # Destroy the library
    ep.libDestroy()

#
# main()
#
if __name__ == "__main__":
  pjsua2_test()
