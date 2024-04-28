-- Crear la secuencia
CREATE SEQUENCE user_id_seq
    START WITH 1
    INCREMENT BY 1;

-- Crear el trigger
CREATE OR REPLACE TRIGGER user_id_trigger
    BEFORE INSERT ON "user"
    FOR EACH ROW
BEGIN
    SELECT user_id_seq.NEXTVAL
    INTO :new.ID_USER
    FROM dual;
END;