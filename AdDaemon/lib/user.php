<?
include_once('db.php');

class User {
  public static function me() {
    return $_SESSION['id'] ?? false;
  }

  public static function create($data) {
    if(!empty($data['password'])) {
      $data['password'] = password_hash($data['password']);
    }
    $user_id = db_insert('users', $data);
    if($user_id) {
      email('welcome', $user, $data);
      return $user_id;
    }
  }

  public static function update($user = false, $data = []) {
    $user = $user ?? self::me();
    return db_update($user, $data);
  }

  public static function login($email, $pass) {
    if(! ($user = Get::user(['email' => $email]) ) ) {
      throw new Exception("$email not found");
    }
    if( password_hash($pass) != $user['password'] )  {
      throw new Exception("User password incorrect");
    }
    $_SESSION['id'] = $user['id'];
    return true;
  }

  public static function logout() {
    session_destroy();
  }
};
