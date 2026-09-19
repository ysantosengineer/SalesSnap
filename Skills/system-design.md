# System design

The intended future data flow is:

```text
User → Company → Datasets → Sales → Analytics → ML Results → AI Insights
```

Expected future domains are authentication, companies, datasets, products, customers, sales, analytics, RFM, forecasting, anomalies, inventory risk, AI insights, and AI chat. This is design documentation only: do not implement these modules in Stage 1.

Keep APIs stateless where practical and the database as the source of truth. Plan future isolation by company. Separate data processing from presentation. An LLM must not replace SQL, Pandas, or ML algorithms; it is primarily an interpretation and natural-language layer. Give modules clear responsibilities and choose simple solutions before distributed infrastructure.
