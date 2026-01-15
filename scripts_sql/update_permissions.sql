
/*
Actualizamos el usuario creado, para que sea administrador
*/

UPDATE public.permissions as perm_up 
SET is_admin = true
   ,can_edit_schedule = true
,can_edit_price = true
FROM public.permissions as perm
WHERE 1 = 1
  AND perm.user_id = 1;