var myform = doit(false, {
  container: 'campaign-info',
  schema: { 
    'title': 'text',
    'organization_id': 'integer',
    'brand_id': 'integer',
  },
  fillNhide: ['organization_id', 'brand_id'],
});
