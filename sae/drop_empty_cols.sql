
DO $$
DECLARE
    col TEXT;
    sql TEXT;
BEGIN
    FOR col IN
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = 'sae'
          AND table_name = 'psy_detail'
    LOOP
        EXECUTE format('SELECT COUNT(*) FROM sae.psy_detail WHERE %I IS NOT NULL', col)
        INTO STRICT sql;

        IF sql::BIGINT = 0 THEN
            --EXECUTE format('ALTER TABLE your_table DROP COLUMN %I', col);
            RAISE NOTICE 'Colonne supprimée : %', col;
        END IF;
    END LOOP;
END
$$;