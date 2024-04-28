CREATE USER C##TALLER_MEC
  IDENTIFIED BY "root1234"
  DEFAULT TABLESPACE USERS
  TEMPORARY TABLESPACE TEMP;

--asignar cuota ilimitada al tablespace por defecto
ALTER USER C##TALLER_MEC QUOTA UNLIMITED ON USERS;

--Asignar privilegios basicos
GRANT CREATE SESSION TO C##TALLER_MEC;
GRANT CREATE TABLE TO C##TALLER_MEC;
GRANT CREATE VIEW TO C##TALLER_MEC;
GRANT CREATE ANY TRIGGER TO C##TALLER_MEC;
GRANT CREATE ANY PROCEDURE TO C##TALLER_MEC;
GRANT CREATE SEQUENCE TO C##TALLER_MEC;
GRANT CREATE SYNONYM TO C##TALLER_MEC;