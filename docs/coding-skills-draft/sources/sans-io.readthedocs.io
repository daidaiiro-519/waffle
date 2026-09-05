<!DOCTYPE html>

<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" /><meta name="viewport" content="width=device-width, initial-scale=1" />

    <title>Network protocols, sans I/O &#8212; Sans I/O 1.0.0 documentation</title>
    <link rel="stylesheet" type="text/css" href="_static/pygments.css?v=03e43079" />
    <link rel="stylesheet" type="text/css" href="_static/alabaster.css?v=039e1c02" />
    <script data-url_root="./" id="documentation_options" src="_static/documentation_options.js?v=af2ce170"></script>
    <script src="_static/doctools.js?v=888ff710"></script>
    <script src="_static/sphinx_highlight.js?v=4825356b"></script>
    <link rel="index" title="Index" href="genindex.html" />
    <link rel="search" title="Search" href="search.html" />
    <link rel="next" title="Writing I/O-Free (Sans-I/O) Protocol Implementations" href="how-to-sans-io.html" />
   
  <link rel="stylesheet" href="_static/custom.css" type="text/css" />
  
  
  <meta name="viewport" content="width=device-width, initial-scale=0.9, maximum-scale=0.9" />

  <script async type="text/javascript" src="/_/static/javascript/readthedocs-addons.js"></script><meta name="readthedocs-project-slug" content="sans-io" /><meta name="readthedocs-version-slug" content="latest" /><meta name="readthedocs-resolver-filename" content="/" /><meta name="readthedocs-http-status" content="200" /></head><body>
  

    <div class="document">
      <div class="documentwrapper">
        <div class="bodywrapper">
          

          <div class="body" role="main">
            
  <section id="network-protocols-sans-i-o">
<h1>Network protocols, sans I/O<a class="headerlink" href="#network-protocols-sans-i-o" title="Permalink to this heading">¶</a></h1>
<p>This page is to provide a single location for people to reference when
looking for network protocol implementations written in Python that
perform <strong>no</strong> I/O (this means libraries that operate directly on
text or bytes; this excludes libraries that just abstract out I/O).</p>
<section id="why">
<h2>Why?<a class="headerlink" href="#why" title="Permalink to this heading">¶</a></h2>
<p>In a word: <em>reusability</em>.
By implementing network protocols without any I/O and instead
operating on bytes or text alone, libraries allow for reuse by other
code regardless of their I/O decisions.
In other words by leaving I/O out of the picture a network protocol
library allows itself to be used by both synchronous and asynchronous
I/O code.
And by not simply abstracting out the I/O it allows users of the
library to drive the network interactions themselves, not the network
protocol library itself; not forcing I/O code to have to conform to a
certain API provides the greatest flexibility for users of such
low-level details such as network protocols.
Working towards this unbinding of network protocols from I/O is very
important as the Python community migrates from synchronous I/O code
to using <code class="docutils literal notranslate"><span class="pre">async</span></code>/<code class="docutils literal notranslate"><span class="pre">await</span></code> for asynchronous I/O.</p>
<p><a class="reference external" href="https://www.youtube.com/watch?v=7cC3_jGwl_U">Cory Benfield’s PyCon US 2016 talk</a>
provides a nice overview as to why designing protocol implementations
this way is important and the best way to do so going forward for the
Python community.</p>
</section>
<section id="more-detail">
<h2>More Detail<a class="headerlink" href="#more-detail" title="Permalink to this heading">¶</a></h2>
<p>For more detail, see the following documents:</p>
<div class="toctree-wrapper compound">
<ul>
<li class="toctree-l1"><a class="reference internal" href="how-to-sans-io.html">Writing I/O-Free (Sans-I/O) Protocol Implementations</a><ul>
<li class="toctree-l2"><a class="reference internal" href="how-to-sans-io.html#what-is-an-i-o-free-protocol-implementation">What Is An I/O-Free Protocol Implementation?</a></li>
<li class="toctree-l2"><a class="reference internal" href="how-to-sans-io.html#why-write-i-o-free-protocol-implementations">Why Write I/O-Free Protocol Implementations?</a></li>
<li class="toctree-l2"><a class="reference internal" href="how-to-sans-io.html#how-to-write-i-o-free-protocol-implementations">How To Write I/O-Free Protocol Implementations</a></li>
<li class="toctree-l2"><a class="reference internal" href="how-to-sans-io.html#integrating-with-i-o">Integrating With I/O</a></li>
<li class="toctree-l2"><a class="reference internal" href="how-to-sans-io.html#acknowledgements">Acknowledgements</a></li>
</ul>
</li>
</ul>
</div>
</section>
<section id="implementations">
<h2>Implementations<a class="headerlink" href="#implementations" title="Permalink to this heading">¶</a></h2>
<table class="docutils align-default">
<thead>
<tr class="row-odd"><th class="head"><p>Protocol</p></th>
<th class="head"><p>Project</p></th>
</tr>
</thead>
<tbody>
<tr class="row-even"><td><p><a class="reference external" href="https://htmlpreview.github.io/?https://github.com/FastCGI-Archives/FastCGI.com/blob/master/docs/FastCGI%20Specification.html">FastCGI</a></p></td>
<td><p><a class="reference external" href="https://github.com/agronholm/fcgiproto">fcgiproto</a></p></td>
</tr>
<tr class="row-odd"><td><p><a class="reference external" href="https://http2.github.io/">HTTP/2</a></p></td>
<td><p><a class="reference external" href="https://github.com/python-hyper/hyper-h2">hyper-h2</a></p></td>
</tr>
<tr class="row-even"><td><p><a class="reference external" href="https://tools.ietf.org/html/rfc7230">HTTP/1.1</a></p></td>
<td><p><a class="reference external" href="https://github.com/python-hyper/h11">h11</a></p></td>
</tr>
<tr class="row-odd"><td><p><a class="reference external" href="https://tools.ietf.org/html/rfc2812">IRC</a></p></td>
<td><p><a class="reference external" href="https://github.com/agronholm/ircproto">ircproto</a></p></td>
</tr>
<tr class="row-even"><td><p><a class="reference external" href="https://tools.ietf.org/html/rfc5849">OAuth 1.0</a> &amp; <a class="reference external" href="https://tools.ietf.org/html/rfc6749">OAuth 2.0</a></p></td>
<td><p><a class="reference external" href="https://github.com/idan/oauthlib">oauthlib</a></p></td>
</tr>
<tr class="row-odd"><td><p><a class="reference external" href="http://tools.ietf.org/html/rfc6455">WebSocket</a></p></td>
<td><p><a class="reference external" href="https://github.com/python-hyper/wsproto">wsproto</a></p></td>
</tr>
<tr class="row-even"><td><p><a class="reference external" href="https://tools.ietf.org/html/rfc1928">SOCKSv5</a></p></td>
<td><p><a class="reference external" href="https://github.com/mike820324/socks5">socks5</a></p></td>
</tr>
<tr class="row-odd"><td><p><a class="reference external" href="https://ftp.icm.edu.pl/packages/socks/socks4/SOCKS4.protocol">SOCKSv4</a> &amp; <a class="reference external" href="https://tools.ietf.org/html/rfc1928">SOCKSv5</a></p></td>
<td><p><a class="reference external" href="https://github.com/pohmelie/siosocks">siosocks</a></p></td>
</tr>
<tr class="row-even"><td><p><a class="reference external" href="https://tools.ietf.org/html/rfc2217">RFC 2217 (Serial over IP)</a></p></td>
<td><p><a class="reference external" href="https://pythonhosted.org/pyserial/pyserial_api.html#serial.rfc2217.PortManager">pyserial</a></p></td>
</tr>
<tr class="row-odd"><td><p><a class="reference external" href="https://epics.anl.gov/base/R3-16/0-docs/CAproto/index.html">EPICS Channel Access</a></p></td>
<td><p><a class="reference external" href="https://nsls-ii.github.io/caproto">caproto</a></p></td>
</tr>
<tr class="row-even"><td><p><a class="reference external" href="https://www.fixtrading.org/standards/fix-5-0-sp-2/">FIX 4.0 - 5.0</a></p></td>
<td><p><a class="reference external" href="https://github.com/da4089/simplefix">simplefix</a></p></td>
</tr>
<tr class="row-odd"><td><p><a class="reference external" href="https://quicwg.org/">QUIC &amp; HTTP/3</a></p></td>
<td><p><a class="reference external" href="https://github.com/aiortc/aioquic">aioquic</a></p></td>
</tr>
<tr class="row-even"><td><p><a class="reference external" href="https://microsoft.github.io/language-server-protocol/">Language Server Protocol</a></p></td>
<td><p><a class="reference external" href="https://github.com/WindSoilder/lsp">lsp</a></p></td>
</tr>
<tr class="row-odd"><td><p><a class="reference external" href="https://tools.ietf.org/html/rfc5321">SMTP</a></p></td>
<td><p><a class="reference external" href="https://github.com/agronholm/smtpproto">smtpproto</a></p></td>
</tr>
<tr class="row-even"><td><p><a class="reference external" href="https://mqtt.org">MQTTv5</a></p></td>
<td><p><a class="reference external" href="https://github.com/empicano/mqtt5">mqtt5</a></p></td>
</tr>
<tr class="row-odd"><td><p><a class="reference external" href="https://www.freedesktop.org/wiki/Software/dbus/">D-Bus</a></p></td>
<td><p><a class="reference external" href="https://gitlab.com/takluyver/jeepney/">jeepney</a></p></td>
</tr>
<tr class="row-even"><td><p><a class="reference external" href="https://www.thorlabs.com/newgrouppage9.cfm?objectgroup_id=9019">Thorlabs APT</a></p></td>
<td><p><a class="reference external" href="https://gitlab.com/yaq/thorlabs-apt-protocol">thorlabs-apt-protocol</a></p></td>
</tr>
<tr class="row-odd"><td><p><a class="reference external" href="https://matrix.org/">Matrix</a></p></td>
<td><p><a class="reference external" href="https://github.com/poljar/matrix-nio">matrix-nio</a></p></td>
</tr>
<tr class="row-even"><td><p><a class="reference external" href="https://tlswg.org/">SSL/TLS</a></p></td>
<td><p><a class="reference external" href="https://docs.python.org/3/library/ssl.html#memory-bio-support">cpython</a></p></td>
</tr>
<tr class="row-odd"><td><p><a class="reference external" href="https://www.rfc-editor.org/rfc/rfc7578">multipart/form-data</a></p></td>
<td><p><a class="reference external" href="https://github.com/defnull/multipart">multipart</a></p></td>
</tr>
</tbody>
</table>
</section>
<section id="libraries">
<h2>Libraries<a class="headerlink" href="#libraries" title="Permalink to this heading">¶</a></h2>
<p>There are also some libraries that help to implement network protocols without
performing any I/O:</p>
<blockquote>
<div><ul class="simple">
<li><p><a class="reference external" href="https://github.com/acatton/ohneio">ohneio</a> (network protocol parsing; <a class="reference external" href="https://ohneio.readthedocs.io/en/latest/getting_started.html#getting-started">Getting started</a>)</p></li>
<li><p><a class="reference external" href="https://gidgethub.readthedocs.io/">gidgethub</a> (GitHub API)</p></li>
</ul>
</div></blockquote>
</section>
</section>


          </div>
          
        </div>
      </div>
      <div class="sphinxsidebar" role="navigation" aria-label="main navigation">
        <div class="sphinxsidebarwrapper">
<h1 class="logo"><a href="#">Sans I/O</a></h1>








<h3>Navigation</h3>
<ul>
<li class="toctree-l1"><a class="reference internal" href="how-to-sans-io.html">Writing I/O-Free (Sans-I/O) Protocol Implementations</a></li>
</ul>

<div class="relations">
<h3>Related Topics</h3>
<ul>
  <li><a href="#">Documentation overview</a><ul>
      <li>Next: <a href="how-to-sans-io.html" title="next chapter">Writing I/O-Free (Sans-I/O) Protocol Implementations</a></li>
  </ul></li>
</ul>
</div>
<div id="searchbox" style="display: none" role="search">
  <h3 id="searchlabel">Quick search</h3>
    <div class="searchformwrapper">
    <form class="search" action="search.html" method="get">
      <input type="text" name="q" aria-labelledby="searchlabel" autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false"/>
      <input type="submit" value="Go" />
    </form>
    </div>
</div>
<script>document.getElementById('searchbox').style.display = "block"</script>








        </div>
      </div>
      <div class="clearer"></div>
    </div>
    <div class="footer">
      &copy;2016, Brett Cannon.
      
      |
      Powered by <a href="http://sphinx-doc.org/">Sphinx 7.1.2</a>
      &amp; <a href="https://github.com/bitprophet/alabaster">Alabaster 0.7.13</a>
      
      |
      <a href="_sources/index.rst.txt"
          rel="nofollow">Page source</a>
    </div>

    

    
  </body>
</html>