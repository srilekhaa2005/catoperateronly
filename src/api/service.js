import { request } from './client';

const mockOperator = { id:3, name:'Raj Kumar', employee_code:'OP-1042', preferred_language:'en', role:'operator' };
const mockMachine = { id:7, machine_code:'EXC-204', machine_type:'excavator', model:'CAT 320', status:'active' };
const mockTasks = [
 {id:101,task_type:'trenching',site_zone:'Zone B',status:'assigned',scheduled_date:'2026-09-23',estimated_duration_minutes:95,actual_duration_minutes:null,machine:mockMachine},
 {id:102,task_type:'material_loading',site_zone:'Zone A',status:'in_progress',scheduled_date:'2026-09-23',estimated_duration_minutes:70,actual_duration_minutes:null,machine:{...mockMachine,id:8,machine_code:'LD-118',machine_type:'loader',model:'CAT 950'}} ,
 {id:103,task_type:'site_grading',site_zone:'Zone C',status:'completed',scheduled_date:'2026-09-23',estimated_duration_minutes:80,actual_duration_minutes:76,machine:mockMachine}
];
const now = Date.now();
const mockReadings = Array.from({length:20},(_,i)=>({id:88231-i,recorded_at:new Date(now-(19-i)*60000).toISOString(),engine_temp_c:92+i%5,hydraulic_pressure_psi:2420+i*7,fuel_level_pct:64-i*.25,rpm:1750+(i%4)*35,idle_time_seconds:i%6===0?40:0,vibration_level:1.02+(i%3)*.08,load_weight_kg:2900+(i%5)*120,ambient_temp_c:34,seatbelt_status:true,proximity_distance_m:7+i%4,safety_alert_triggered:false,is_anomaly:i===17,anomaly_score:i===17?.82:.05}));
let mockAlerts=[{id:555,machine_id:7,task_id:101,alert_type:'hydraulic_overheat',severity:'critical',status:'open',detected_at:new Date(now-8*60000).toISOString()},{id:554,machine_id:7,task_id:101,alert_type:'proximity_warning',severity:'warning',status:'open',detected_at:new Date(now-22*60000).toISOString()}];

async function withMock(apiCall, fallback) { try { return await apiCall(); } catch { return fallback(); } }
export const api = {
 operator: id => withMock(()=>request(`/operators/${id}`),()=>mockOperator),
 updateLanguage: (id, language) => withMock(()=>request(`/operators/${id}`,{method:'PATCH',body:JSON.stringify({preferred_language:language})}),()=>({...mockOperator,preferred_language:language})),
 tasks: id => withMock(()=>request(`/operators/${id}/tasks`),()=>({tasks:mockTasks})),
 startTask: id => withMock(()=>request(`/tasks/${id}/start`,{method:'POST'}),()=>({id,status:'in_progress',started_at:new Date().toISOString()})),
 completeTask: id => withMock(()=>request(`/tasks/${id}/complete`,{method:'POST'}),()=>({id,status:'completed',actual_duration_minutes:mockTasks.find(t=>t.id===id)?.estimated_duration_minutes||60,completed_at:new Date().toISOString()})),
 estimate: id => withMock(()=>request(`/tasks/${id}/estimate`),()=>({task_id:id,estimated_duration_minutes:mockTasks.find(t=>t.id===id)?.estimated_duration_minutes||60,model_version:'task_time_v1',inputs_used:{task_type:'trenching',machine_type:'excavator',site_zone:'Zone B',weather_condition:'clear',operator_experience_years:4.5,historical_avg_duration_minutes:91}})),
 readings: id => withMock(()=>request(`/machines/${id}/readings/latest?count=20`),()=>({machine_id:id,readings:mockReadings})),
 machines: ()=>withMock(()=>request('/machines'),()=>({machines:[mockMachine,{id:8,machine_code:'LD-118',machine_type:'loader',model:'CAT 950',status:'active'},{id:9,machine_code:'DZ-302',machine_type:'dozer',model:'CAT D6',status:'idle'}]})),
 alerts: id => withMock(()=>request(`/operators/${id}/alerts?status=open`),()=>({alerts:mockAlerts})),
 alert: id => withMock(()=>request(`/alerts/${id}`),()=>({id:555,machine_id:7,task_id:101,operator_id:3,alert_type:'hydraulic_overheat',severity:'critical',status:'open',detected_at:mockAlerts[0].detected_at,reading:{engine_temp_c:118.3,hydraulic_pressure_psi:3100,anomaly_score:.91}})),
 explain: (id,lang='en')=>withMock(()=>request(`/alerts/${id}/explain?lang=${lang}`),()=>({alert_id:id,language:lang,explanation:lang==='ta'?'ஹைட்ராலிக் அழுத்தம் பாதுகாப்பு வரம்பைத் தாண்டியது.':'Hydraulic pressure and temperature exceeded the safe operating range.',recommended_action:lang==='ta'?'இயந்திரத்தை நிறுத்தி ஹைட்ராலிக் அமைப்பைச் சரிபார்க்கவும்.':'Stop the machine and inspect the hydraulic system before continuing.',source_language:'en'})),
 patchAlert:(id,status)=>withMock(()=>request(`/alerts/${id}`,{method:'PATCH',body:JSON.stringify({status})}),()=>({id,status,acknowledged_at:new Date().toISOString()})),
 training:(type,lang='en')=>withMock(()=>request(`/training-content?${type ? `alert_type=${encodeURIComponent(type)}&` : ''}lang=${encodeURIComponent(lang)}`),()=>({content:[{id:12,title:lang==='ta'?'ஹைட்ராலிக் அமைப்பு பாதுகாப்பு':'Hydraulic System Safety',body_text:'Monitor temperature and pressure. Stop the machine when readings exceed the safe operating range.',related_alert_type:type,language:lang}]})),
 incidents: id => withMock(()=>request(`/operators/${id}/incidents`),()=>({incidents:[]})),
 createIncident: body => withMock(()=>request('/incidents',{method:'POST',body:JSON.stringify(body)}),()=>({id:41,...body,created_at:new Date().toISOString()})),
 scenario:(machine_id,scenario,duration_seconds=60)=>withMock(()=>request('/simulator/scenario',{method:'POST',body:JSON.stringify({machine_id,scenario,duration_seconds})}),()=>({status:'scenario_started',machine_id,scenario}))
};
