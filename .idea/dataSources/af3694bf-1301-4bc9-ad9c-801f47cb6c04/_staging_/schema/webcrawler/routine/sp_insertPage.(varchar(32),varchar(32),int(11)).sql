DELIMITER //

CREATE PROCEDURE `sp_insertPage` (
  IN pageurl MEDIUMTEXT,
  IN word MEDIUMTEXT,
  IN counts MEDIUMINT
)
LANGUAGE SQL
DETERMINISTIC
SQL SECURITY DEFINER
BEGIN
  INSERT INTO tb_pages(
    url,
    wordName,
    countWords
  ) VALUES (
    pageurl,
    word,
    counts
  );
END//