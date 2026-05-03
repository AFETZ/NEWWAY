/* -*-  Mode: C++; c-file-style: "gnu"; indent-tabs-mode:nil; -*- */
/*
 * 5G NR-V2X PHY Metrics Experiment
 *
 * Based on v2v-cam-exchange-sionna-nrv2x template.
 * Captures detailed PHY-layer metrics from PSSCH and PSCCH trace sources
 * into CSV files for offline analysis, alongside CAM-level metrics and PRR.
 *
 * Optional Sionna ray-tracing channel model via --sionna=1.
 */

#include "ns3/vector.h"
#include "ns3/string.h"
#include "ns3/socket.h"
#include "ns3/double.h"
#include "ns3/config.h"
#include "ns3/log.h"
#include "ns3/command-line.h"
#include "ns3/sumo_xml_parser.h"
#include "ns3/BSMap.h"
#include "ns3/caBasicService.h"
#include "ns3/gn-utils.h"
#include "ns3/traci-module.h"
#include "ns3/config-store.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/applications-module.h"
#include "ns3/mobility-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/nr-module.h"
#include "ns3/lte-module.h"
#include "ns3/stats-module.h"
#include "ns3/config-store-module.h"
#include "ns3/log.h"
#include "ns3/antenna-module.h"
#include <bitset>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <limits>
#include <mutex>
#include <sstream>
#include <unordered_map>
#include <vector>
#include "ns3/sumo_xml_parser.h"
#include "ns3/vehicle-visualizer-module.h"
#include "ns3/MetricSupervisor.h"
#include "ns3/sionna-helper.h"
#include <unistd.h>
#include "ns3/core-module.h"

using namespace ns3;

NS_LOG_COMPONENT_DEFINE ("V2V5gPhyMetricsExperiment");

// ──────────────────── Global state ────────────────────
static std::string g_outPrefix = "5g-phy-metrics";
static std::ofstream g_psschFile;
static std::ofstream g_pscchFile;
static std::ofstream g_psschTxFile;
static std::ofstream g_pscchTxFile;
static std::ofstream g_camFile;
static bool g_psschHeaderWritten = false;
static bool g_pscchHeaderWritten = false;
static bool g_psschTxHeaderWritten = false;
static bool g_pscchTxHeaderWritten = false;
static bool g_camHeaderWritten = false;

BSMap basicServices;
static int packet_count = 0;

// ──────────────────── Helper: bitmap parser ────────────────────
void
GetSlBitmapFromString (std::string slBitMapString, std::vector<std::bitset<1>> &slBitMapVector)
{
  static std::unordered_map<std::string, uint8_t> lookupTable =
      {
          {"0", 0},
          {"1", 1},
      };

  std::stringstream ss (slBitMapString);
  std::string token;
  std::vector<std::string> extracted;

  while (std::getline (ss, token, '|'))
    {
      extracted.push_back (token);
    }

  for (const auto &v : extracted)
    {
      if (lookupTable.find (v) == lookupTable.end ())
        {
          NS_FATAL_ERROR ("Bit type " << v << " not valid. Valid values are: 0 and 1");
        }
      slBitMapVector.push_back (lookupTable[v] & 0x01);
    }
}

// ──────────────────── PSSCH trace callback ────────────────────
void
NotifySlPsschRx (const SlRxDataPacketTraceParams params)
{
  if (!g_psschHeaderWritten)
    {
      g_psschFile << "time_ms,rx_rnti,tx_rnti,frame,subframe,slot,"
                     "sinr_db,sinr_min_db,mcs,tbler,tb_size_bytes,corrupt,"
                     "ndi,tbler_sci2,sci2_corrupted,"
                     "rb_start,rb_end,rb_assigned,bwp_id,rv,"
                     "dst_l2_id,src_l2_id"
                  << std::endl;
      g_psschHeaderWritten = true;
    }

  g_psschFile << std::fixed << std::setprecision (4)
              << params.m_timeMs << ","
              << params.m_rnti << ","
              << params.m_txRnti << ","
              << params.m_frameNum << ","
              << static_cast<int> (params.m_subframeNum) << ","
              << params.m_slotNum << ","
              << 10.0 * std::log10 (params.m_sinr) << ","
              << 10.0 * std::log10 (params.m_sinrMin) << ","
              << static_cast<int> (params.m_mcs) << ","
              << params.m_tbler << ","
              << params.m_tbSize << ","
              << (params.m_corrupt ? 1 : 0) << ","
              << static_cast<int> (params.m_ndi) << ","
              << params.m_tblerSci2 << ","
              << (params.m_sci2Corrupted ? 1 : 0) << ","
              << params.m_rbStart << ","
              << params.m_rbEnd << ","
              << params.m_rbAssignedNum << ","
              << params.m_bwpId << ","
              << static_cast<int> (params.m_rv) << ","
              << params.m_dstL2Id << ","
              << params.m_srcL2Id
              << std::endl;
}

// ──────────────────── PSCCH trace callback ────────────────────
void
NotifySlPscchRx (const SlRxCtrlPacketTraceParams params)
{
  if (!g_pscchHeaderWritten)
    {
      g_pscchFile << "time_ms,rx_rnti,tx_rnti,frame,subframe,slot,"
                     "sinr_db,sinr_min_db,mcs,tbler,tb_size_bytes,corrupt,"
                     "rb_start,rb_end,rb_assigned,bwp_id,rv,"
                     "priority,reservation_period_ms,"
                     "total_subchannels,start_subchannel,length_subchannel,"
                     "max_num_per_reserve,dst_l2_id"
                  << std::endl;
      g_pscchHeaderWritten = true;
    }

  g_pscchFile << std::fixed << std::setprecision (4)
              << params.m_timeMs << ","
              << params.m_rnti << ","
              << params.m_txRnti << ","
              << params.m_frameNum << ","
              << static_cast<int> (params.m_subframeNum) << ","
              << params.m_slotNum << ","
              << 10.0 * std::log10 (params.m_sinr) << ","
              << 10.0 * std::log10 (params.m_sinrMin) << ","
              << static_cast<int> (params.m_mcs) << ","
              << params.m_tbler << ","
              << params.m_tbSize << ","
              << (params.m_corrupt ? 1 : 0) << ","
              << params.m_rbStart << ","
              << params.m_rbEnd << ","
              << params.m_rbAssignedNum << ","
              << params.m_bwpId << ","
              << static_cast<int> (params.m_rv) << ","
              << static_cast<int> (params.m_priority) << ","
              << params.m_slResourceReservePeriod << ","
              << params.m_totalSubChannels << ","
              << static_cast<int> (params.m_indexStartSubChannel) << ","
              << static_cast<int> (params.m_lengthSubChannel) << ","
              << static_cast<int> (params.m_maxNumPerReserve) << ","
              << params.m_dstL2Id
              << std::endl;
}

// ──────────────────── PSSCH TX trace callback ────────────────────
void
NotifySlPsschTx (const SlPsschUeMacStatParameters params)
{
  if (!g_psschTxHeaderWritten)
    {
      g_psschTxFile << "time_ms,imsi,rnti,frame,subframe,slot,"
                       "sym_start,sym_len,subchannel_size,rb_start,rb_len,"
                       "harq_id,ndi,rv,src_l2_id,dst_l2_id,csi_req,cast_type,"
                       "resource_reselection_counter,c_reselection_counter"
                    << std::endl;
      g_psschTxHeaderWritten = true;
    }

  g_psschTxFile << std::fixed << std::setprecision (4)
                << params.timeMs << ","
                << params.imsi << ","
                << params.rnti << ","
                << params.frameNum << ","
                << params.subframeNum << ","
                << params.slotNum << ","
                << params.symStart << ","
                << params.symLength << ","
                << params.subChannelSize << ","
                << params.rbStart << ","
                << params.rbLength << ","
                << static_cast<int> (params.harqId) << ","
                << static_cast<int> (params.ndi) << ","
                << static_cast<int> (params.rv) << ","
                << params.srcL2Id << ","
                << params.dstL2Id << ","
                << static_cast<int> (params.csiReq) << ","
                << static_cast<int> (params.castType) << ","
                << static_cast<int> (params.resoReselCounter) << ","
                << params.cReselCounter
                << std::endl;
}

// ──────────────────── PSCCH TX trace callback ────────────────────
void
NotifySlPscchTx (const SlPscchUeMacStatParameters params)
{
  if (!g_pscchTxHeaderWritten)
    {
      g_pscchTxFile << "time_ms,imsi,rnti,frame,subframe,slot,"
                       "sym_start,sym_len,rb_start,rb_len,priority,mcs,tb_size_bytes,"
                       "reservation_period_ms,total_subchannels,start_subchannel,"
                       "length_subchannel,max_num_per_reserve,gap_retx1,gap_retx2"
                    << std::endl;
      g_pscchTxHeaderWritten = true;
    }

  g_pscchTxFile << std::fixed << std::setprecision (4)
                << params.timeMs << ","
                << params.imsi << ","
                << params.rnti << ","
                << params.frameNum << ","
                << params.subframeNum << ","
                << params.slotNum << ","
                << params.symStart << ","
                << params.symLength << ","
                << params.rbStart << ","
                << params.rbLength << ","
                << static_cast<int> (params.priority) << ","
                << static_cast<int> (params.mcs) << ","
                << params.tbSize << ","
                << params.slResourceReservePeriod << ","
                << params.totalSubChannels << ","
                << params.slPsschSubChStart << ","
                << params.slPsschSubChLength << ","
                << static_cast<int> (params.slMaxNumPerReserve) << ","
                << static_cast<int> (params.gapReTx1) << ","
                << static_cast<int> (params.gapReTx2)
                << std::endl;
}

// ──────────────────── CAM reception callback ────────────────────
void
receiveCAM (asn1cpp::Seq<CAM> cam, Address from, StationID_t my_stationID,
            StationType_t my_StationType, SignalInfo phy_info)
{
  packet_count++;

  double snr = phy_info.snr;
  double sinr = phy_info.sinr;
  double rssi = phy_info.rssi;
  double rsrp = phy_info.rsrp;

  if (std::isnan (snr) && !std::isnan (sinr))
    snr = sinr;
  if (std::isnan (rssi) && !std::isnan (rsrp))
    rssi = rsrp;

  double distance = std::numeric_limits<double>::quiet_NaN ();
  Ptr<BSContainer> receiverBs = basicServices.get (my_stationID);
  if (receiverBs != nullptr && receiverBs->getTraCIclient () != nullptr)
    {
      try
        {
          libsumo::TraCIPosition pos =
              receiverBs->getTraCIclient ()->TraCIAPI::vehicle.getPosition (
                  "veh" + std::to_string (my_stationID));
          pos = receiverBs->getTraCIclient ()->TraCIAPI::simulation.convertXYtoLonLat (pos.x, pos.y);

          double lat_sender =
              asn1cpp::getField (
                  cam->cam.camParameters.basicContainer.referencePosition.latitude, double) /
              1e7;
          double lon_sender =
              asn1cpp::getField (
                  cam->cam.camParameters.basicContainer.referencePosition.longitude, double) /
              1e7;

          distance = haversineDist (lat_sender, lon_sender, pos.y, pos.x);
        }
      catch (const std::exception &)
        {
          // Vehicle may have already left SUMO while late packets are still being drained.
        }
    }

  if (!g_camHeaderWritten)
    {
      g_camFile << "time_s,tx_id,rx_id,distance_m,rssi_dbm,snr_db" << std::endl;
      g_camHeaderWritten = true;
    }

  g_camFile << std::fixed << std::setprecision (4)
            << Simulator::Now ().GetSeconds () << ","
            << cam->header.stationId << ","
            << my_stationID << ","
            << distance << ","
            << rssi << ","
            << snr
            << std::endl;
}

// ──────────────────── PRR saver ────────────────────
void
savePRRs (Ptr<MetricSupervisor> metSup, uint64_t numberOfNodes)
{
  std::string prrPath = g_outPrefix + "-prr.csv";
  std::ofstream file (prrPath, std::ios::out);
  file << "node_id,prr" << std::endl;
  for (uint64_t i = 1; i <= numberOfNodes; ++i)
    {
      double prr = metSup->getAveragePRR_vehicle (i);
      file << i << "," << std::fixed << std::setprecision (6) << prr << std::endl;
    }
  file.close ();
  std::cout << "PRR data written to " << prrPath << std::endl;
}

// ═══════════════════════════════════ main ═══════════════════════════════════
int
main (int argc, char *argv[])
{
  // ── Default parameters ──
  std::string phyMode ("OfdmRate3MbpsBW10MHz");
  int up = 0;
  bool realtime = false;
  bool verbose = false;
  int numberOfNodes;
  uint32_t nodeCounter = 0;
  double m_baseline_prr = 150.0;
  int txPower = 23;
  double sinr_threshold = 10;
  xmlDocPtr rou_xml_file;
  double simTime = 100.0;

  // NR sidelink parameters
  double centralFrequencyBandSl = 5.89e9;
  uint16_t bandwidthBandSl = 100;
  std::string tddPattern = "UL|UL|UL|UL|UL|UL|UL|UL|UL|UL|";
  std::string slBitMap = "1|1|1|1|1|1|1|1|1|1";
  uint16_t numerologyBwpSl = 2;
  uint16_t slSensingWindow = 100;
  uint16_t slSelectionWindow = 5;
  uint16_t slSubchannelSize = 10;
  uint16_t slMaxNumPerReserve = 3;
  double slProbResourceKeep = 0.0;
  uint16_t slMaxTxTransNumPssch = 5;
  uint16_t reservationPeriod = 20;
  bool enableSensing = false;
  uint16_t t1 = 2;
  uint16_t t2 = 81;
  int slThresPsschRsrp = -128;
  bool enableChannelRandomness = false;
  uint16_t channelUpdatePeriod = 500;
  uint8_t mcs = 14;

  bool sumo_gui = true;
  std::string sumo_folder = "src/automotive/examples/sumo_files_v2v_map/";
  std::string mob_trace = "cars.rou.xml";
  std::string sumo_config = "src/automotive/examples/sumo_files_v2v_map/map.sumo.cfg";
  uint16_t sumo_port = 3400;
  double sumo_wait_for_socket_s = 5.0;
  int64_t sumo_seed = 10;
  std::string outPrefix = "5g-phy-metrics";

  // Sionna parameters
  bool sionna = false;
  std::string sionnaServerIp = "";
  bool sionnaLocalMachine = false;
  bool sionnaVerbose = false;

  // ── CLI ──
  CommandLine cmd (__FILE__);
  cmd.AddValue ("verbose", "Enable verbose PHY logs", verbose);
  cmd.AddValue ("userpriority", "EDCA User Priority", up);
  cmd.AddValue ("baseline", "PRR baseline distance [m]", m_baseline_prr);
  cmd.AddValue ("tx-power", "TX power [dBm]", txPower);
  cmd.AddValue ("sim-time", "Simulation duration [s]", simTime);
  cmd.AddValue ("sumo-gui", "Show SUMO GUI", sumo_gui);
  cmd.AddValue ("sumo-folder", "Folder containing SUMO route file", sumo_folder);
  cmd.AddValue ("mob-trace", "SUMO route file used for vehicle counting", mob_trace);
  cmd.AddValue ("sumo-config", "SUMO config file", sumo_config);
  cmd.AddValue ("sumo-port", "TraCI TCP port for SUMO", sumo_port);
  cmd.AddValue ("sumo-seed", "SUMO seed", sumo_seed);
  cmd.AddValue ("sumo-wait-for-socket-s", "How long to wait for SUMO socket [s]", sumo_wait_for_socket_s);
  cmd.AddValue ("mcs", "Fixed MCS index (0-27)", mcs);
  cmd.AddValue ("numerology", "NR numerology (0-4)", numerologyBwpSl);
  cmd.AddValue ("sensing", "Enable NR SL sensing", enableSensing);
  cmd.AddValue ("channel-randomness", "Enable channel randomness", enableChannelRandomness);
  cmd.AddValue ("subchannel-size", "Subchannel size in RBs", slSubchannelSize);
  cmd.AddValue ("reservation-period", "Resource reservation period [ms]", reservationPeriod);
  cmd.AddValue ("bandwidth", "Bandwidth in RBs", bandwidthBandSl);
  cmd.AddValue ("t1", "Minimum selection window (T1)", t1);
  cmd.AddValue ("t2", "Maximum selection window (T2)", t2);
  cmd.AddValue ("out-prefix", "Output file prefix (path + name prefix)", outPrefix);
  cmd.AddValue ("sionna", "Enable Sionna ray-tracing channel model", sionna);
  cmd.AddValue ("sionna-server-ip", "Sionna server IP address", sionnaServerIp);
  cmd.AddValue ("sionna-local-machine", "Sionna runs on local machine", sionnaLocalMachine);
  cmd.AddValue ("sionna-verbose", "Enable Sionna verbose logging", sionnaVerbose);
  cmd.AddValue ("centralFrequencyBandSl", "The central frequency to be used for Sidelink band/channel", centralFrequencyBandSl);
  cmd.AddValue ("bandwidthBandSl", "The system bandwidth to be used for Sidelink", bandwidthBandSl);
  cmd.AddValue ("txPower", "Total tx power in dBm", txPower);
  cmd.AddValue ("tddPattern", "The TDD pattern string", tddPattern);
  cmd.AddValue ("slBitMap", "The sidelink bitmap string", slBitMap);
  cmd.AddValue ("numerologyBwpSl", "The numerology to be used in sidelink bandwidth part", numerologyBwpSl);
  cmd.AddValue ("slSensingWindow", "The sidelink sensing window length in ms", slSensingWindow);
  cmd.AddValue ("slSelectionWindow", "The sidelink selection window length in physical slots", slSelectionWindow);
  cmd.AddValue ("slSubchannelSize", "The sidelink subchannel size in RBs", slSubchannelSize);
  cmd.AddValue ("slMaxNumPerReserve", "Maximum number of reserved PSCCH/PSSCH resources per SCI", slMaxNumPerReserve);
  cmd.AddValue ("slProbResourceKeep", "Probability with which the UE keeps the current resource", slProbResourceKeep);
  cmd.AddValue ("slMaxTxTransNumPssch", "Maximum transmission number for PSSCH", slMaxTxTransNumPssch);
  cmd.AddValue ("ReservationPeriod", "The resource reservation period in ms", reservationPeriod);
  cmd.AddValue ("enableSensing", "Enable sidelink sensing-based resource selection", enableSensing);
  cmd.AddValue ("slThresPsschRsrp", "RSRP threshold for sensing-based sidelink selection", slThresPsschRsrp);
  cmd.AddValue ("enableChannelRandomness", "Enable shadowing and channel updates", enableChannelRandomness);
  cmd.AddValue ("channelUpdatePeriod", "Channel update period in ms", channelUpdatePeriod);
  cmd.Parse (argc, argv);

  g_outPrefix = outPrefix;

  std::cout << "=== 5G NR-V2X PHY Metrics Experiment ===" << std::endl;
  std::cout << "MCS=" << static_cast<int> (mcs)
            << " numerology=" << numerologyBwpSl
            << " txPower=" << txPower << " dBm"
            << " sensing=" << (enableSensing ? "ON" : "OFF")
            << " sionna=" << (sionna ? "ON" : "OFF")
            << " simTime=" << simTime << " s"
            << std::endl;

  // ── Open output CSV files ──
  g_psschFile.open (g_outPrefix + "-pssch.csv", std::ios::out);
  g_pscchFile.open (g_outPrefix + "-pscch.csv", std::ios::out);
  g_psschTxFile.open (g_outPrefix + "-pssch-tx.csv", std::ios::out);
  g_pscchTxFile.open (g_outPrefix + "-pscch-tx.csv", std::ios::out);
  g_camFile.open (g_outPrefix + "-cam.csv", std::ios::out);

  if (!g_psschFile.is_open () || !g_pscchFile.is_open () ||
      !g_psschTxFile.is_open () || !g_pscchTxFile.is_open () || !g_camFile.is_open ())
    {
      NS_FATAL_ERROR ("Cannot open output CSV files with prefix: " << g_outPrefix);
    }

  // ── Sionna ray-tracing channel model ──
  SionnaHelper& sionnaHelper = SionnaHelper::GetInstance ();
  if (sionna)
    {
      sionnaHelper.SetSionna (sionna);
      sionnaHelper.SetServerIp (sionnaServerIp);
      sionnaHelper.SetLocalMachine (sionnaLocalMachine);
      sionnaHelper.SetVerbose (sionnaVerbose);
      std::cout << "Sionna ray-tracing enabled (server=" << sionnaServerIp
                << ", local=" << (sionnaLocalMachine ? "yes" : "no") << ")" << std::endl;
    }

  // ── Load SUMO topology ──
  xmlInitParser ();
  std::string path = sumo_folder + mob_trace;
  rou_xml_file = xmlParseFile (path.c_str ());
  if (rou_xml_file == NULL)
    {
      NS_FATAL_ERROR ("Error: unable to parse XML file: " << path);
    }
  numberOfNodes = XML_rou_count_vehicles (rou_xml_file);
  xmlFreeDoc (rou_xml_file);
  xmlCleanupParser ();

  if (numberOfNodes == -1)
    {
      NS_FATAL_ERROR ("Cannot get vehicle count from: " << path);
    }

  Ptr<TraciClient> sumoClient = CreateObject<TraciClient> ();

  if (sionna)
    {
      sumoClient->SetSionnaUp ();
    }
  uint64_t numberOfNodes_nr = numberOfNodes;

  Ptr<MetricSupervisor> metSup_nr = NULL;
  MetricSupervisor metSupObj_nr (m_baseline_prr);
  metSup_nr = &metSupObj_nr;
  metSup_nr->setTraCIClient (sumoClient);

  MobilityHelper mobility;
  Time slBearersActivationTime = Seconds (2.0);
  NS_ABORT_IF (centralFrequencyBandSl > 6e9);

  Config::SetDefault ("ns3::LteRlcUm::MaxTxBufferSize", UintegerValue (999999999));

  if (realtime)
    GlobalValue::Bind ("SimulatorImplementationType",
                       StringValue ("ns3::RealtimeSimulatorImpl"));

  Ptr<NrPointToPointEpcHelper> epcHelper = CreateObject<NrPointToPointEpcHelper> ();
  Ptr<NrHelper> nrHelper = CreateObject<NrHelper> ();

  NodeContainer nrNodes;
  nrNodes.Create (numberOfNodes_nr);
  mobility.Install (nrNodes);

  nrHelper->SetEpcHelper (epcHelper);

  BandwidthPartInfoPtrVector allBwps;
  CcBwpCreator ccBwpCreator;
  const uint8_t numCcPerBand = 1;

  CcBwpCreator::SimpleOperationBandConf bandConfSl (centralFrequencyBandSl, bandwidthBandSl,
                                                     numCcPerBand,
                                                     BandwidthPartInfo::V2V_Highway);
  OperationBandInfo bandSl = ccBwpCreator.CreateOperationBandContiguousCc (bandConfSl);

  if (enableChannelRandomness)
    {
      Config::SetDefault ("ns3::ThreeGppChannelModel::UpdatePeriod",
                          TimeValue (MilliSeconds (channelUpdatePeriod)));
      nrHelper->SetChannelConditionModelAttribute ("UpdatePeriod",
                                                    TimeValue (MilliSeconds (channelUpdatePeriod)));
      nrHelper->SetPathlossAttribute ("ShadowingEnabled", BooleanValue (true));
    }
  else
    {
      Config::SetDefault ("ns3::ThreeGppChannelModel::UpdatePeriod",
                          TimeValue (MilliSeconds (0)));
      nrHelper->SetChannelConditionModelAttribute ("UpdatePeriod",
                                                    TimeValue (MilliSeconds (0)));
      nrHelper->SetPathlossAttribute ("ShadowingEnabled", BooleanValue (false));
    }

  nrHelper->InitializeOperationBand (&bandSl);
  allBwps = CcBwpCreator::GetAllBwps ({bandSl});

  nrHelper->SetUeAntennaAttribute ("NumRows", UintegerValue (1));
  nrHelper->SetUeAntennaAttribute ("NumColumns", UintegerValue (2));
  nrHelper->SetUeAntennaAttribute ("AntennaElement",
                                    PointerValue (CreateObject<IsotropicAntennaModel> ()));

  nrHelper->SetUePhyAttribute ("TxPower", DoubleValue (txPower));
  nrHelper->SetUePhyAttribute ("RiSinrThreshold1", DoubleValue (sinr_threshold));
  nrHelper->SetUePhyAttribute ("RiSinrThreshold2", DoubleValue (sinr_threshold));

  nrHelper->SetUeMacAttribute ("EnableSensing", BooleanValue (enableSensing));
  nrHelper->SetUeMacAttribute ("T1", UintegerValue (static_cast<uint8_t> (t1)));
  nrHelper->SetUeMacAttribute ("T2", UintegerValue (t2));
  nrHelper->SetUeMacAttribute ("ActivePoolId", UintegerValue (0));
  nrHelper->SetUeMacAttribute ("ReservationPeriod", TimeValue (MilliSeconds (reservationPeriod)));
  nrHelper->SetUeMacAttribute ("NumSidelinkProcess", UintegerValue (4));
  nrHelper->SetUeMacAttribute ("EnableBlindReTx", BooleanValue (true));
  nrHelper->SetUeMacAttribute ("SlThresPsschRsrp", IntegerValue (slThresPsschRsrp));

  uint8_t bwpIdForGbrMcptt = 0;

  nrHelper->SetBwpManagerTypeId (TypeId::LookupByName ("ns3::NrSlBwpManagerUe"));
  nrHelper->SetUeBwpManagerAlgorithmAttribute ("GBR_MC_PUSH_TO_TALK",
                                                UintegerValue (bwpIdForGbrMcptt));

  std::set<uint8_t> bwpIdContainer;
  bwpIdContainer.insert (bwpIdForGbrMcptt);

  NetDeviceContainer allSlUesNetDeviceContainer =
      nrHelper->InstallUeDevice (nrNodes, allBwps);

  for (auto it = allSlUesNetDeviceContainer.Begin ();
       it != allSlUesNetDeviceContainer.End (); ++it)
    {
      DynamicCast<NrUeNetDevice> (*it)->UpdateConfig ();
    }

  Ptr<NrSlHelper> nrSlHelper = CreateObject<NrSlHelper> ();
  nrSlHelper->SetEpcHelper (epcHelper);

  std::string errorModel = "ns3::NrLteMiErrorModel";
  nrSlHelper->SetSlErrorModel (errorModel);
  nrSlHelper->SetUeSlAmcAttribute ("AmcModel", EnumValue (NrAmc::ErrorModel));

  nrSlHelper->SetNrSlSchedulerTypeId (NrSlUeMacSchedulerSimple::GetTypeId ());
  nrSlHelper->SetUeSlSchedulerAttribute ("FixNrSlMcs", BooleanValue (true));
  nrSlHelper->SetUeSlSchedulerAttribute ("InitialNrSlMcs", UintegerValue (mcs));

  nrSlHelper->PrepareUeForSidelink (allSlUesNetDeviceContainer, bwpIdContainer);

  // ── Resource pool configuration ──
  LteRrcSap::SlResourcePoolNr slResourcePoolNr;
  Ptr<NrSlCommPreconfigResourcePoolFactory> ptrFactory =
      Create<NrSlCommPreconfigResourcePoolFactory> ();

  std::vector<std::bitset<1>> slBitMapVector;
  GetSlBitmapFromString (slBitMap, slBitMapVector);
  NS_ABORT_MSG_IF (slBitMapVector.empty (), "GetSlBitmapFromString failed");
  ptrFactory->SetSlTimeResources (slBitMapVector);
  ptrFactory->SetSlSensingWindow (slSensingWindow);
  ptrFactory->SetSlSelectionWindow (slSelectionWindow);
  ptrFactory->SetSlFreqResourcePscch (10);
  ptrFactory->SetSlSubchannelSize (slSubchannelSize);
  ptrFactory->SetSlMaxNumPerReserve (slMaxNumPerReserve);
  LteRrcSap::SlResourcePoolNr pool = ptrFactory->CreatePool ();
  slResourcePoolNr = pool;

  LteRrcSap::SlResourcePoolConfigNr slresoPoolConfigNr;
  slresoPoolConfigNr.haveSlResourcePoolConfigNr = true;
  uint16_t poolId = 0;
  LteRrcSap::SlResourcePoolIdNr slResourcePoolIdNr;
  slResourcePoolIdNr.id = poolId;
  slresoPoolConfigNr.slResourcePoolId = slResourcePoolIdNr;
  slresoPoolConfigNr.slResourcePool = slResourcePoolNr;

  LteRrcSap::SlBwpPoolConfigCommonNr slBwpPoolConfigCommonNr;
  slBwpPoolConfigCommonNr.slTxPoolSelectedNormal[slResourcePoolIdNr.id] = slresoPoolConfigNr;

  LteRrcSap::Bwp bwp;
  bwp.numerology = numerologyBwpSl;
  bwp.symbolsPerSlots = 14;
  bwp.rbPerRbg = 1;
  bwp.bandwidth = bandwidthBandSl;

  LteRrcSap::SlBwpGeneric slBwpGeneric;
  slBwpGeneric.bwp = bwp;
  slBwpGeneric.slLengthSymbols = LteRrcSap::GetSlLengthSymbolsEnum (14);
  slBwpGeneric.slStartSymbol = LteRrcSap::GetSlStartSymbolEnum (0);

  LteRrcSap::SlBwpConfigCommonNr slBwpConfigCommonNr;
  slBwpConfigCommonNr.haveSlBwpGeneric = true;
  slBwpConfigCommonNr.slBwpGeneric = slBwpGeneric;
  slBwpConfigCommonNr.haveSlBwpPoolConfigCommonNr = true;
  slBwpConfigCommonNr.slBwpPoolConfigCommonNr = slBwpPoolConfigCommonNr;

  LteRrcSap::SlFreqConfigCommonNr slFreConfigCommonNr;
  for (const auto &it : bwpIdContainer)
    {
      slFreConfigCommonNr.slBwpList[it] = slBwpConfigCommonNr;
    }

  LteRrcSap::TddUlDlConfigCommon tddUlDlConfigCommon;
  tddUlDlConfigCommon.tddPattern = tddPattern;

  LteRrcSap::SlPreconfigGeneralNr slPreconfigGeneralNr;
  slPreconfigGeneralNr.slTddConfig = tddUlDlConfigCommon;

  LteRrcSap::SlUeSelectedConfig slUeSelectedPreConfig;
  NS_ABORT_MSG_UNLESS (slProbResourceKeep <= 1.0, "slProbResourceKeep must be in [0,1]");
  slUeSelectedPreConfig.slProbResourceKeep = slProbResourceKeep;

  LteRrcSap::SlPsschTxParameters psschParams;
  psschParams.slMaxTxTransNumPssch = static_cast<uint8_t> (slMaxTxTransNumPssch);
  LteRrcSap::SlPsschTxConfigList pscchTxConfigList;
  pscchTxConfigList.slPsschTxParameters[0] = psschParams;
  slUeSelectedPreConfig.slPsschTxConfigList = pscchTxConfigList;

  LteRrcSap::SidelinkPreconfigNr slPreConfigNr;
  slPreConfigNr.slPreconfigGeneral = slPreconfigGeneralNr;
  slPreConfigNr.slUeSelectedPreConfig = slUeSelectedPreConfig;
  slPreConfigNr.slPreconfigFreqInfoList[0] = slFreConfigCommonNr;

  nrSlHelper->InstallNrSlPreConfiguration (allSlUesNetDeviceContainer, slPreConfigNr);

  int64_t stream = 1;
  stream += nrHelper->AssignStreams (allSlUesNetDeviceContainer, stream);
  stream += nrSlHelper->AssignStreams (allSlUesNetDeviceContainer, stream);

  // ── All nodes are both TX and RX ──
  NodeContainer txSlUes;
  NodeContainer rxSlUes;
  NetDeviceContainer txSlUesNetDevice;
  NetDeviceContainer rxSlUesNetDevice;
  txSlUes.Add (nrNodes);
  rxSlUes.Add (nrNodes);
  txSlUesNetDevice.Add (allSlUesNetDeviceContainer);
  rxSlUesNetDevice.Add (allSlUesNetDeviceContainer);

  InternetStackHelper internet;
  internet.Install (nrNodes);
  uint32_t dstL2Id = 255;
  Ipv4Address groupAddress4 ("225.0.0.0");

  Address remoteAddress;
  Address localAddress;
  uint16_t port = 8000;
  Ptr<LteSlTft> tft;

  Ipv4InterfaceContainer ueIpIface;
  ueIpIface = epcHelper->AssignUeIpv4Address (allSlUesNetDeviceContainer);

  Ipv4StaticRoutingHelper ipv4RoutingHelper;
  for (uint32_t u = 0; u < nrNodes.GetN (); ++u)
    {
      Ptr<Node> ueNode = nrNodes.Get (u);
      Ptr<Ipv4StaticRouting> ueStaticRouting =
          ipv4RoutingHelper.GetStaticRouting (ueNode->GetObject<Ipv4> ());
      ueStaticRouting->SetDefaultRoute (epcHelper->GetUeDefaultGatewayAddress (), 1);
    }
  remoteAddress = InetSocketAddress (groupAddress4, port);
  localAddress = InetSocketAddress (Ipv4Address::GetAny (), port);

  tft = Create<LteSlTft> (LteSlTft::Direction::TRANSMIT, LteSlTft::CommType::GroupCast,
                           groupAddress4, dstL2Id);
  nrSlHelper->ActivateNrSlBearer (slBearersActivationTime, allSlUesNetDeviceContainer, tft);

  tft = Create<LteSlTft> (LteSlTft::Direction::RECEIVE, LteSlTft::CommType::GroupCast,
                           groupAddress4, dstL2Id);
  nrSlHelper->ActivateNrSlBearer (slBearersActivationTime, allSlUesNetDeviceContainer, tft);

  // ──────────────────── Connect PHY trace sources ────────────────────
  Config::ConnectWithoutContext (
      "/NodeList/*/DeviceList/*/$ns3::NrUeNetDevice/ComponentCarrierMapUe/*/NrUeMac/"
      "SlPsschScheduling",
      MakeCallback (&NotifySlPsschTx));

  Config::ConnectWithoutContext (
      "/NodeList/*/DeviceList/*/$ns3::NrUeNetDevice/ComponentCarrierMapUe/*/NrUeMac/"
      "SlPscchScheduling",
      MakeCallback (&NotifySlPscchTx));

  Config::ConnectWithoutContext (
      "/NodeList/*/DeviceList/*/$ns3::NrUeNetDevice/ComponentCarrierMapUe/*/NrUePhy/"
      "NrSpectrumPhyList/*/RxPsschTraceUe",
      MakeCallback (&NotifySlPsschRx));

  Config::ConnectWithoutContext (
      "/NodeList/*/DeviceList/*/$ns3::NrUeNetDevice/ComponentCarrierMapUe/*/NrUePhy/"
      "NrSpectrumPhyList/*/RxPscchTraceUe",
      MakeCallback (&NotifySlPscchRx));

  std::cout << "PHY trace sources connected (PSSCH + PSCCH)" << std::endl;

  // ── SUMO setup ──
  sumoClient->SetAttribute ("SumoConfigPath", StringValue (sumo_config));
  sumoClient->SetAttribute ("SumoBinaryPath", StringValue (""));
  sumoClient->SetAttribute ("SynchInterval", TimeValue (Seconds (0.01)));
  sumoClient->SetAttribute ("StartTime", TimeValue (Seconds (0.0)));
  sumoClient->SetAttribute ("SumoGUI", BooleanValue (sumo_gui));
  sumoClient->SetAttribute ("SumoPort", UintegerValue (sumo_port));
  sumoClient->SetAttribute ("PenetrationRate", DoubleValue (1.0));
  sumoClient->SetAttribute ("SumoLogFile", BooleanValue (false));
  sumoClient->SetAttribute ("SumoStepLog", BooleanValue (false));
  sumoClient->SetAttribute ("SumoSeed", IntegerValue (sumo_seed));
  sumoClient->SetAttribute ("SumoWaitForSocket", TimeValue (Seconds (sumo_wait_for_socket_s)));

  std::cout << "TX power: " << txPower << " dBm" << std::endl;
  std::cout << "Starting simulation..." << std::endl;

  STARTUP_FCN setupNewWifiNode = [&] (std::string vehicleID,
                                       TraciClient::StationTypeTraCI_t stationType) -> Ptr<Node>
  {
    (void) stationType;
    unsigned long vehID = std::stol (vehicleID.substr (3));
    if (nodeCounter >= nrNodes.GetN ())
      {
        NS_FATAL_ERROR ("Node pool empty while creating " << vehicleID);
      }

    Ptr<NetDevice> netDevice;
    Ptr<Socket> sock;
    TypeId tid = TypeId::LookupByName ("ns3::UdpSocketFactory");
    Ptr<Node> includedNode = nrNodes.Get (nodeCounter);
    ++nodeCounter;
    sock = Socket::CreateSocket (includedNode, tid);
    if (sock->Bind (InetSocketAddress (Ipv4Address::GetAny (), 19)) == -1)
      {
        NS_FATAL_ERROR ("Failed to bind client socket for NR-V2X");
      }
    Ipv4Address groupAddress4 ("225.0.0.0");
    sock->Connect (InetSocketAddress (groupAddress4, 19));

    netDevice = includedNode->GetDevice (0);
    Ptr<NrUeNetDevice> nrDevice = DynamicCast<NrUeNetDevice> (netDevice);
    nrHelper->GetUePhy (netDevice, 0)->SetRiSinrThreshold1 (sinr_threshold);
    nrHelper->GetUePhy (netDevice, 0)->SetRiSinrThreshold2 (sinr_threshold);
    nrDevice->GetPhy (0)->GetSpectrumPhy ()->GetSpectrumChannel ()->SetAttribute (
        "MaxLossDb", DoubleValue (128.0));

    Ptr<BSContainer> bs_container =
        CreateObject<BSContainer> (vehID, StationType_passengerCar, sumoClient, false, sock);
    bs_container->addCAMRxCallback (
        std::bind (&receiveCAM, std::placeholders::_1, std::placeholders::_2,
                   std::placeholders::_3, std::placeholders::_4, std::placeholders::_5));
    bs_container->linkMetricSupervisor (metSup_nr);
    bs_container->disablePRRSupervisorForGNBeacons ();
    bs_container->setupContainer (true, false, false, false);
    basicServices.add (bs_container);
    std::srand (Simulator::Now ().GetNanoSeconds () * 2);
    double desync = ((double) std::rand () / RAND_MAX);
    bs_container->getCABasicService ()->startCamDissemination (desync);

    return includedNode;
  };

  SHUTDOWN_FCN shutdownWifiNode = [] (Ptr<Node> exNode, std::string vehicleID)
  {
    Ptr<ConstantPositionMobilityModel> mob =
        exNode->GetObject<ConstantPositionMobilityModel> ();
    mob->SetPosition (Vector (-1000.0 + (rand () % 25), 320.0 + (rand () % 25), 250.0));
    unsigned long intVehicleID = std::stol (vehicleID.substr (3));

    Ptr<BSContainer> bsc = basicServices.get (intVehicleID);
    if (bsc != nullptr)
      {
        bsc->cleanup ();
      }
    basicServices.remove (intVehicleID);
  };

  sumoClient->SumoSetup (setupNewWifiNode, shutdownWifiNode);

  Simulator::Stop (Seconds (simTime));
  auto start_time = std::chrono::high_resolution_clock::now ();
  Simulator::Run ();

  std::cout << "Simulation finished." << std::endl;

  // ── Save summary ──
  std::string summaryPath = g_outPrefix + "-summary.txt";
  std::ofstream summaryFile (summaryPath, std::ios::out);
  summaryFile << "5G NR-V2X PHY Metrics Experiment Summary" << std::endl;
  summaryFile << "========================================" << std::endl;
  summaryFile << "MCS: " << static_cast<int> (mcs) << std::endl;
  summaryFile << "Numerology: " << numerologyBwpSl << std::endl;
  summaryFile << "TX Power: " << txPower << " dBm" << std::endl;
  summaryFile << "Sensing: " << (enableSensing ? "ON" : "OFF") << std::endl;
  summaryFile << "Sionna: " << (sionna ? "ON" : "OFF") << std::endl;
  summaryFile << "Sim Time: " << simTime << " s" << std::endl;
  summaryFile << "Vehicles: " << numberOfNodes << std::endl;
  summaryFile << "Total CAMs received: " << packet_count << std::endl;
  summaryFile << "Average PRR: " << metSup_nr->getAveragePRR_overall () << std::endl;
  summaryFile << "Average latency (ms): " << metSup_nr->getAverageLatency_overall ()
              << std::endl;
  summaryFile << "RX packets: " << metSup_nr->getNumberRx_overall () << std::endl;
  summaryFile << "TX packets: " << metSup_nr->getNumberTx_overall () << std::endl;

  auto end_time = std::chrono::high_resolution_clock::now ();
  std::chrono::duration<double> elapsed = end_time - start_time;
  summaryFile << "Wall-clock time: " << elapsed.count () << " s" << std::endl;
  summaryFile.close ();
  std::cout << "Summary written to " << summaryPath << std::endl;

  savePRRs (metSup_nr, numberOfNodes);

  // Close CSV files
  g_psschFile.close ();
  g_pscchFile.close ();
  g_psschTxFile.close ();
  g_pscchTxFile.close ();
  g_camFile.close ();

  std::cout << "CSV files written:" << std::endl;
  std::cout << "  PSSCH: " << g_outPrefix << "-pssch.csv" << std::endl;
  std::cout << "  PSCCH: " << g_outPrefix << "-pscch.csv" << std::endl;
  std::cout << "  PSSCH TX: " << g_outPrefix << "-pssch-tx.csv" << std::endl;
  std::cout << "  PSCCH TX: " << g_outPrefix << "-pscch-tx.csv" << std::endl;
  std::cout << "  CAM:   " << g_outPrefix << "-cam.csv" << std::endl;
  std::cout << "  PRR:   " << g_outPrefix << "-prr.csv" << std::endl;

  Simulator::Destroy ();

  return 0;
}
