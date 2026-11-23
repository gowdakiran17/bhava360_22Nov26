-- Local fixtures only. Stable synthetic IDs make replay safe.
INSERT INTO places(city, aliases, name_kn, name_hi, native_review, latitude, longitude, iana_zone)
VALUES
 ('Bengaluru','{Bengaluru,Bangalore}','ಬೆಂಗಳೂರು','बेंगलुरु','pending',12.97,77.59,'Asia/Kolkata'),
 ('Mysuru','{Mysuru,Mysore}','ಮೈಸೂರು','मैसूर','pending',12.30,76.64,'Asia/Kolkata'),
 ('Delhi','{Delhi}','ದೆಹಲಿ','दिल्ली','pending',28.61,77.21,'Asia/Kolkata'),
 ('Mumbai','{Mumbai}','ಮುಂಬೈ','मुंबई','pending',19.08,72.88,'Asia/Kolkata'),
 ('Chennai','{Chennai}','ಚೆನ್ನೈ','चेन्नई','pending',13.08,80.27,'Asia/Kolkata'),
 ('Mangaluru','{Mangaluru,Mangalore}','ಮಂಗಳೂರು','मंगलुरु','pending',12.91,74.86,'Asia/Kolkata'),
 ('Kalaburagi','{Kalaburagi,Gulbarga}','ಕಲಬುರಗಿ','कलबुर्गी','pending',17.33,76.83,'Asia/Kolkata')
ON CONFLICT (city) DO NOTHING;

CREATE TEMP TABLE fixture ON COMMIT DROP AS
SELECT md5('fixture:user:' || name)::uuid AS user_id, name, birth::date, born::time, city
FROM (VALUES
 ('Asha','1992-03-12','05:40','Bengaluru'), ('Ravi','1985-08-03','14:10','Mysuru'),
 ('Meera','2001-12-21','22:30','Delhi'), ('Kabir','1978-06-09','07:15','Mumbai'),
 ('Dev','1995-01-05','12:00','Chennai')
) AS f(name,birth,born,city);

INSERT INTO users(id) SELECT user_id FROM fixture ON CONFLICT DO NOTHING;
INSERT INTO identities(user_id,kind,identifier_digest)
SELECT user_id,'email',encode(sha256(convert_to(lower(name) || '@example.test','UTF8')),'hex')
FROM fixture ON CONFLICT DO NOTHING;
INSERT INTO identities(user_id,kind,identifier_digest)
SELECT user_id,'phone',encode(sha256(convert_to('+91900000000' ||
  array_position(ARRAY['Asha','Ravi','Meera','Kabir','Dev'],name)::text,'UTF8')),'hex')
FROM fixture ON CONFLICT DO NOTHING;
INSERT INTO profiles(id,user_id,display_name,local_date,local_time,iana_zone,place_id,birth_instant,time_precision,relation)
SELECT md5('fixture:profile:' || name || precision)::uuid,user_id,name,birth,born,p.iana_zone,p.id,
       (birth + born) AT TIME ZONE p.iana_zone,precision::birth_precision,'self'
FROM fixture JOIN places p USING (city)
CROSS JOIN (VALUES ('known'),('unknown')) AS variant(precision)
WHERE precision='known' OR name='Dev'
ON CONFLICT DO NOTHING;

INSERT INTO staff_users(email,role) VALUES
 ('owner@example.test','owner'),('admin@example.test','admin'),
 ('reviewer@example.test','astrologer-reviewer'),('kn-reviewer@example.test','native-language reviewer'),
 ('tester@example.test','tester'),('support@example.test','support')
ON CONFLICT DO NOTHING;

UPDATE staff_users SET assigned_locale='kn' WHERE email='kn-reviewer@example.test' AND assigned_locale IS NULL;
UPDATE staff_users SET fixture_user_id=md5('fixture:user:Asha')::uuid
WHERE email='tester@example.test' AND fixture_user_id IS NULL;
