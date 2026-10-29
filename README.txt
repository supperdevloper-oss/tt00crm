Paraveda CRM — manual Tracking column only

Upload these files to public_html:
- index.html
- api.php
- digylog-admin.html

Behavior:
- COMONDES has an editable Tracking column. Staff type/paste a tracking manually per order.
- LIVRAISON displays the same manually entered tracking.
- Tracking can be used in the CRM search/filter.
- Entering/editing Tracking never changes Suivie/livraison, dateLiv, Livrée, or Retour.
- The inbound Digylog webhook remains disabled and cannot modify CRM rows.
- No phone matching, automatic tracking import, or automatic Digylog status synchronization is included.
- Current crm_data.json is not included or overwritten.
