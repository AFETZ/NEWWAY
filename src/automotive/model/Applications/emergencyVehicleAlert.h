#ifndef EMERGENCYVEHICLEALERT_H
#define EMERGENCYVEHICLEALERT_H

#include "ns3/MetricSupervisor.h"

#include "ns3/application.h"
#include "ns3/asn_utils.h"

#include <unordered_map>

#include "ns3/denBasicService.h"
#include "ns3/caBasicService.h"
#include "ns3/cpBasicService.h"
#include "ns3/cpBasicService_v1.h"
#include "ns3/vdpTraci.h"
#include "ns3/socket.h"
#include "ns3/random-variable-stream.h"
#include "ns3/signalInfoUtils.h"

#include "ns3/sumo-sensor.h"
#include "ns3/LDM.h"
#include "ns3/traci-client.h"
#include <fstream>
#include <cstdint>
#include <limits>
#include <map>
#include <vector>
namespace ns3 {

class emergencyVehicleAlert : public Application
{
  public:

    /**
     * \brief Get the type ID.
     * \return the object TypeId
     */
    static TypeId GetTypeId (void);

    emergencyVehicleAlert ();

    virtual ~emergencyVehicleAlert ();

    void StopApplicationNow ();

    /**
     * \brief Callback to handle a CAM reception.
     *
     * This function is called everytime a packet is received by the CABasicService.
     *
     * \param the ASN.1 CAM structure containing the info of the packet that was received.
     */
    void receiveCAM (asn1cpp::Seq<CAM> cam, Address from, StationId_t my_stationID, StationType_t my_StationType, SignalInfo phy_info);

    /**
     * \brief Callback to handle a DENM reception.
     *
     * This function is called everytime a packet is received by the DENBasicService.
     *
     * \param the denData structure containing the info of the packet that was received.
     */
    void receiveDENM (denData denm, Address from);

    /**
     * \brief Callback to handle a CPM reception.
     *
     * This function is called everytime a packet is received by the CPBasicService.
     *
     * \param the ASN.1 CPM structure containing the info of the packet that was received.
     */
    void receiveCPM (asn1cpp::Seq<CollectivePerceptionMessage> cpm, Address from);

    /**
     * \brief Callback to handle a CPM reception.
     *
     * This function is called everytime a packet is received by the CPBasicService.
     *
     * \param the ASN.1 CPM structure containing the info of the packet that was received.
     */
    void receiveCPMV1 (asn1cpp::Seq<CPMV1> cpm, Address from);

  protected:
    virtual void DoDispose (void);

  private:

    DENBasicService m_denService; //!< DEN Basic Service object
    CABasicService m_caService; //!< CA Basic Service object
    CPBasicService m_cpService; //!< CP Basic Service object
    CPBasicServiceV1 m_cpService_v1; //!< CP Basic Service object version 1 (for CPMv1)
    Ptr<btp> m_btp; //! BTP object
    Ptr<GeoNet> m_geoNet; //! GeoNetworking Object
    Ptr<SUMOSensor> m_sensor;
    Ptr<LDM> m_LDM; //! LDM object
    Ipv4Address m_ipAddress; //!< C-V2X self IP address (set by 'v2v-cv2x.cc')
    Ptr<Socket> m_socket; //!< Socket TX/RX for everything
    std::string m_model; //!< Communication Model (possible values: 80211p and cv2x)

    /**
     * \brief Send a new updated DENM (i.e. call appDENM_update as foreseen by ETSI EN 302 637-3 V1.3.1)
     *
     * This function can be called to send a DENM containing updated information, with the
     * same ActionID, after sending the first DENM with TriggerDenm()
     *
     */
    void UpdateDenm(ActionID_t actionid);

    /**
     * \brief Trigger a new DENM (i.e. call appDENM_trigger as foreseen by ETSI EN 302 637-3 V1.3.1)
     *
     * This function can be called to send a new DENM.
     *
     */
    void TriggerDenm(void);
    void logCamTx (asn1cpp::Seq<CAM> cam);
    void LogControlEvent (const std::string& eventType,
                          long txId,
                          long msgSeq,
                          uint64_t packetUid,
                          double distanceMeters,
                          double headingDiffDeg,
                          int laneBefore,
                          int laneAfter,
                          double speedTarget);
    void LogPhyDropEvent (const GeoNet::RxPhyDropInfo& dropInfo);
    static void PublishCamTxEvent (long txId, long msgSeq, double txTimeS);
    void OnGlobalCamTxEvent (long txId, long msgSeq, double txTimeS);
    void EvaluateCamSilenceInference (long txId, long msgSeq);
    void EmitInferredCamDropNoAction (long txId, long msgSeq, const std::string& dropType);
    void CamSilenceWatchdogTick ();
    void SensorWatchdogTick ();
    uint64_t BuildSyntheticPktUid (long txId, long msgSeq) const;
    void MaybeTriggerCrashModeOnNoActionDrop (long txId, long msgSeq, uint64_t packetUid);
    void GrantJunctionAwareness ();
    bool ApplyEvasiveControl (const std::string& eventType,
                              long txId,
                              long msgSeq,
                              uint64_t packetUid,
                              double distanceMeters,
                              double headingDiffDeg);
    struct PerVehiclePrrProfile
    {
      double rx_drop_prob_phy_cam = 0.0;
      double rx_drop_prob_phy_cpm = std::numeric_limits<double>::quiet_NaN ();
      double equiv_tx_power_dbm = std::numeric_limits<double>::quiet_NaN ();
      double target_prr = std::numeric_limits<double>::quiet_NaN ();
    };
    bool TryGetPerVehiclePrrProfile (const std::string& vehicleId, PerVehiclePrrProfile& outProfile) const;


    /**
     * \brief Set the maximum speed of the current vehicle
     *
     * This function rolls back the speed of the vehicle, turning it to its original value.
     * It also change the color of the vehicle to yellow (i.e. the default vehicle color)
     *
     */
    void SetMaxSpeed ();

    vehicleData_t translateCPMV1data(asn1cpp::Seq<CPMV1> cpm, int objectIndex);
    vehicleData_t translateCPMdata(asn1cpp::Seq<CollectivePerceptionMessage> cpm,asn1cpp::Seq<PerceivedObject> object, int objectIndex);

    virtual void StartApplication (void);
    virtual void StopApplication (void);

    double m_distance_threshold;
    double m_heading_threshold;
    int m_reaction_target_lane;
    double m_reaction_speed_factor_target_lane;
    double m_reaction_speed_factor_other_lane;
    double m_reaction_action_duration_s;
    double m_cpm_distance_threshold;
    double m_cpm_ttc_threshold_s;
    bool m_sensor_reaction_enable;
    double m_sensor_reaction_distance_threshold_m;
    double m_sensor_reaction_ttc_threshold_s;
    double m_sensor_reaction_period_ms;
    double m_sensor_range_m;
    std::string m_sensor_reaction_focus_vehicle_id;
    int64_t m_sensor_reaction_focus_station_id;
    double m_control_action_cooldown_s;
    bool m_reaction_force_lane_change_enable;
    double m_last_control_action_s;

    Ptr<TraciClient> m_client; //!< TraCI client
    std::string m_id; //!< vehicle id
    std::string m_type; //!< vehicle type
    double m_max_speed; //!< To save initial veh max speed
    double m_denm_intertime; //!< Time between two consecutives DENMs
    bool m_print_summary; //!< To print a small summary when vehicle leaves the simulation
    bool m_already_print; //!< To avoid printing two summaries
    bool m_real_time; //!< To decide wheter to use realtime scheduler
    std::string m_csv_name; //!< CSV log file name
    std::ofstream m_csv_ofstream_cam; //!< CSV log stream (CAM), created using m_csv_name
    std::ofstream m_csv_ofstream_msg; //!< CSV log stream (TX/RX events), created using m_csv_name
    std::ofstream m_csv_ofstream_ctrl; //!< CSV log stream (vehicle control events)
    std::ofstream m_csv_ofstream_profile; //!< CSV log stream (configured per-vehicle PHY/PRR profile)
    std::ofstream m_csv_ofstream_phy; //!< CSV log stream (PHY-level metrics per received message)

    /* Counters */
    int m_cam_received;
    int m_cpm_received;
    int m_cam_dropped_app;
    int m_cpm_dropped_app;
    int m_cam_dropped_phy;
    int m_cpm_dropped_phy;
    int m_denm_sent;
    int m_denm_received;
    uint64_t m_control_actions;

    EventId m_speed_ev; //!< Event to change the vehicle speed
    EventId m_send_denm_ev; //!< Event to send the DENM
    EventId m_send_cam_ev; //!< Event to send the CAM
    EventId m_update_denm_ev; //!< Event to update the DENM

    bool m_send_cam;
    bool m_send_cpm;
    double m_rx_drop_prob_cam;
    double m_rx_drop_prob_cpm;
    double m_rx_drop_prob_phy_cam;
    double m_rx_drop_prob_phy_cpm;
    bool m_drop_triggered_reaction_enable;
    bool m_target_loss_profile_enable;
    std::string m_target_loss_vehicle_id;
    double m_target_loss_rx_drop_prob_cam;
    double m_target_loss_rx_drop_prob_cpm;
    double m_target_loss_rx_drop_prob_phy_cam;
    double m_target_loss_rx_drop_prob_phy_cpm;
    bool m_target_loss_profile_applied;
    std::string m_per_vehicle_prr_profile;
    bool m_per_vehicle_prr_profile_applied;
    double m_profile_equiv_tx_power_dbm;
    double m_profile_target_prr;
    bool m_cam_silence_drop_inference_enable;
    int64_t m_cam_silence_focus_tx_id;
    double m_cam_silence_expected_period_ms;
    double m_cam_silence_timeout_s;
    double m_cam_silence_bootstrap_time_s;
    bool m_cam_silence_seen_any;
    int64_t m_cam_silence_last_msg_seq;
    int64_t m_cam_silence_next_msg_seq;
    int64_t m_cam_silence_last_emitted_seq;
    double m_cam_silence_last_rx_time_s;
    double m_cam_silence_last_inferred_time_s;
    std::map<std::pair<long, long>, double> m_pending_cam_tx_time_s;
    EventId m_cam_silence_watchdog_ev;
    EventId m_sensor_watchdog_ev;
    static std::vector<emergencyVehicleAlert*> s_active_instances;
    Ptr<UniformRandomVariable> m_drop_rv;
    bool m_crash_mode_enable;
    std::string m_crash_mode_vehicle_id;
    uint32_t m_crash_mode_no_action_threshold;
    double m_crash_mode_force_speed_mps;
    double m_crash_mode_duration_s;
    double m_crash_mode_min_time_s;
    uint32_t m_drop_no_action_streak;
    bool m_crash_mode_active;
    EventId m_crash_mode_restore_ev;

    bool m_v2x_awareness_junction_enable;
    bool m_v2x_junction_awareness_granted;

    Ptr<MetricSupervisor> m_metric_supervisor = nullptr;

  };

} // namespace ns3

#endif /* EMERGENCYVEHICLEALERT_H */
