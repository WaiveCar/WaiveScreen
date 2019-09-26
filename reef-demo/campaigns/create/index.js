doit(false, {
  container: 'campaign-info',
  schema: { 
    'campaign title': 'text',
    'organization_id': 'integer',
    'brand_id': 'integer',
  },
  permissions: {
    'organization_id': 'p-admin',
  }
});
