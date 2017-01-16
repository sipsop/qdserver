class uwsgi {

    $mount_point = "/var/www/qdserver"

    $params = {
        "ini"      => "server.ini",
        "module"   => "main",
        "callable" => "app",
    }

    python::pip { 'uwsgi' :
        url => 'http://projects.unbit.it/downloads/uwsgi-lts.tar.gz'
    }

    file { "/etc/systemd/system/uwsgi.service":
        ensure  => present,
        owner   => "root",
        group   => "root",
        mode    => "0644",
        content => template("uwsgi/uwsgi.service"),
    }

    file { "/etc/init/uwsgi.conf":
        ensure  => present,
        owner   => "root",
        group   => "root",
        mode    => "0644",
        content => template("uwsgi/uwsgi.conf.erb"),
    }

    file { "/var/log/uwsgi.log":
        ensure  => present,
        owner   => "www-data",
        group   => "www-data",
        mode    => "0755",
        require => User["www-data"],
    }

    service { "uwsgi":
        ensure     => running,
        enable     => true,
        require    => [File["/etc/systemd/system/uwsgi.service"], File["/var/log/uwsgi.log"]],
    }
}
