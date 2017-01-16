class nginx {

    package { 'nginx':
        ensure => present,
        before => File['/etc/nginx/sites-available/default'],
    }

    file { '/etc/nginx/sites-available/default':
        ensure  => file,
        owner   => 'root',
        group   => 'root',
        mode    => '640',
        content => template('nginx/default_site.erb'),
        notify  => Service['nginx'],
    }

    file { '/etc/nginx/nginx.conf':
        ensure  => file,
        owner   => 'root',
        group   => 'root',
        mode    => '640',
        content => template('nginx/nginx.conf.erb'),
        notify  => Service['nginx'],
    }

    service { 'nginx':
        ensure     => running,
        enable     => true,
        hasstatus  => true,
        hasrestart => true,
        subscribe  => File['/etc/nginx/sites-available/default'],
    }
}
