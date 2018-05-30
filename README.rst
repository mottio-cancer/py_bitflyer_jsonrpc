.. -*- mode: rst -*-

py_bitflyer_jsonrpc
==========

''py_bitflyer_jsonrpc''　は、仮想通貨取引所 Bitflyer のJSON-RPCプロトコルを使用して情報を取得するライブラリです。

Install
-------
Using pip

.. code::

  $ pip install git+https://github.com/mottio-cancer/py_bitflyer_jsonrpc.git


Usage
-----

.. code:: python

  import py_bitflyer_jsonrpc
  api = py_bitflyer_jsonrpc.BitflyerJSON_RPC(symbol=product_code)
  """
  or you can select the information you want to enable, as shown below.
  The default for target_channels is this.

  api = py_bitflyer_jsonrpc.BitflyerJSON_RPC(symbol=product_code,
                                             target_channels=("board_snapshot", "tickers", "executions"))

  But "board_snapshot" is somewhat large, you may want to not subscribing for resource savings.
  write that.

  api = py_bitflyer_jsonrpc.BitflyerJSON_RPC(symbol=product_code,
                                             target_channels=("tickers", "executions"))

  """


Example
-------

Order Book Infomaition
~~~~~~~~~~

.. code:: python

  # 現在のオーダー情報のスナップショットを取得します
  # スナップショットは、JSON-RPCを通して配信される更新情報を購読し、常に最新の状態に更新しています
  snapshot = api.get_board_snapshot()

Ticker
~~~~~~

.. code:: python

  # 最新のTicker情報を取得します
  ticker = api.get_ticker()

Execution Order 
~~~~~~~~~~~~~~~~


.. code:: python

  # 直近最大1000件の約定情報を取得します
  executions = api.get_excution()

  # 指定した''order_acceptance_id''に対応した約定情報が存在すれば、その配列を返します
  executions = api.get_execution(order_acceptance_id=ORDER_ACCEPTANCE_ID)
  # ''order_acceptance_id''に対応する約定が配信されていない場合は空の配列を返却するので、
  # 下記のように注文の約定を待つことに使用できます
  while not api.get_execution(order_acceptance_id=ORDER_ACCEPTANCE_ID):
    time.sleep(0.1)
  

More detail
~~~~~~~~~~~

JSON-RPCの仕様について詳しく知りたければ、下記を参照してください。
: https://lightning.bitflyer.jp/docs#json-rpc-2.0-over-websocket

Author
------

@mottio-cancer (<mottio.cancer@gmail.com>)
