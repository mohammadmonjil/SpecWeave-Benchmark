// Auto-flattened Verilog file

// ===== Macros =====
`define ETH_PHY_ADDR                 5'h01
`define LED_CFG1                     1'b0
`define LED_CFG2                     1'b0
`define LED_CFG3                     1'b1
`define SUPPORTED_SPEED_AND_PORT     7'h3F
`define EXTENDED_STATUS              1'b0
`define DEFAULT_STATUS               7'h09
`define PHY_ID1                      16'h0013
`define PHY_ID2                      6'h1E
`define MAN_MODEL_NUM                6'h0E
`define MAN_REVISION_NUM             4'h2
`define WB_FREQ 0.100
`define MEM_FREQ 0.100
`define Tsetup 4
`define Thold  1
`define WAIT_FOR_RESPONSE 1023
`define MAX_BLK_SIZE  1024
`define WB_TB_MAX_RTY 0
`define WB_ADDR_WIDTH 32
`define WB_DATA_WIDTH 32
`define WB_SEL_WIDTH `WB_DATA_WIDTH/8
`define WB_TAG_WIDTH 5
`define WB_ADDR_TYPE [(`WB_ADDR_WIDTH - 1):0]
`define WB_DATA_TYPE [(`WB_DATA_WIDTH - 1):0]
`define WB_SEL_TYPE  [(`WB_SEL_WIDTH  - 1):0]
`define WB_TAG_TYPE  [(`WB_TAG_WIDTH  - 1):0]
`define READ_STIM_TYPE [(`WB_ADDR_WIDTH + `WB_SEL_WIDTH + `WB_TAG_WIDTH - 1):0]
`define READ_STIM_LENGTH (`WB_ADDR_WIDTH + `WB_SEL_WIDTH + `WB_TAG_WIDTH)
`define READ_ADDRESS  [(`WB_ADDR_WIDTH - 1):0]
`define READ_SEL      [(`WB_ADDR_WIDTH + `WB_SEL_WIDTH - 1):`WB_ADDR_WIDTH]
`define READ_TAG_STIM [(`WB_ADDR_WIDTH + `WB_SEL_WIDTH + `WB_TAG_WIDTH - 1):(`WB_ADDR_WIDTH + `WB_SEL_WIDTH)]
`define READ_RETURN_TYPE [(32 + 4 + `WB_DATA_WIDTH + `WB_TAG_WIDTH - 1):0]
`define READ_DATA        [(32 + `WB_DATA_WIDTH + 4 - 1):32 + 4]
`define READ_TAG_RET     [(32 + 4 + `WB_DATA_WIDTH + `WB_TAG_WIDTH - 1):(`WB_DATA_WIDTH + 32 + 4)]
`define READ_RETURN_LENGTH (32 + 4 + `WB_DATA_WIDTH + `WB_TAG_WIDTH - 1)
`define WRITE_STIM_TYPE [(`WB_ADDR_WIDTH + `WB_DATA_WIDTH + `WB_SEL_WIDTH + `WB_TAG_WIDTH - 1):0]
`define WRITE_ADDRESS       [(`WB_ADDR_WIDTH - 1):0]
`define WRITE_DATA          [(`WB_ADDR_WIDTH + `WB_DATA_WIDTH - 1):`WB_ADDR_WIDTH]
`define WRITE_SEL           [(`WB_ADDR_WIDTH + `WB_DATA_WIDTH + `WB_SEL_WIDTH - 1):(`WB_ADDR_WIDTH + `WB_DATA_WIDTH)]
`define WRITE_TAG_STIM      [(`WB_ADDR_WIDTH + `WB_DATA_WIDTH + `WB_SEL_WIDTH + `WB_TAG_WIDTH - 1):(`WB_ADDR_WIDTH + `WB_DATA_WIDTH + `WB_SEL_WIDTH)]
`define WRITE_STIM_LENGTH (`WB_ADDR_WIDTH + `WB_DATA_WIDTH + `WB_SEL_WIDTH + `WB_TAG_WIDTH)
`define WRITE_RETURN_TYPE [(32 + 4 + `WB_TAG_WIDTH - 1):0]
`define WRITE_TAG_RET     [(32 + 4 + `WB_TAG_WIDTH - 1):32 + 4]
`define TB_ERROR_BIT [0]
`define CYC_ACK [1]
`define CYC_RTY [2]
`define CYC_ERR [3]
`define CYC_RESPONSE [3:1]
`define CYC_ACTUAL_TRANSFER [35:4]
`define WB_TRANSFER_FLAGS [41:0]
`define WB_TRANSFER_SIZE     [41:10]
`define WB_TRANSFER_AUTO_RTY [8]
`define WB_TRANSFER_CAB      [9]
`define INIT_WAITS           [3:0]
`define SUBSEQ_WAITS         [7:4]
`define ACK_RESPONSE  3'b100
`define ERR_RESPONSE  3'b010
`define RTY_RESPONSE  3'b001
`define NO_RESPONSE   3'b000
`define MULTICAST_XFR          0
`define UNICAST_XFR            1
`define BROADCAST_XFR          2
`define UNICAST_WRONG_XFR      3
`define ETH_BASE              32'hd0000000
`define ETH_WIDTH             32'h800
`define MEMORY_BASE           32'h2000
`define MEMORY_WIDTH          32'h10000
`define TX_BUF_BASE           `MEMORY_BASE
`define RX_BUF_BASE           `MEMORY_BASE + 32'h8000
`define TX_BD_BASE            `ETH_BASE + 32'h00000400
`define RX_BD_BASE            `ETH_BASE + 32'h00000600
`define ETH_TX_BD_READY    32'h8000 /* Tx BD Ready */
`define ETH_TX_BD_IRQ      32'h4000 /* Tx BD IRQ Enable */
`define ETH_TX_BD_WRAP     32'h2000 /* Tx BD Wrap (last BD) */
`define ETH_TX_BD_PAD      32'h1000 /* Tx BD Pad Enable */
`define ETH_TX_BD_CRC      32'h0800 /* Tx BD CRC Enable */
`define ETH_TX_BD_UNDERRUN 32'h0100 /* Tx BD Underrun Status */
`define ETH_TX_BD_RETRY    32'h00F0 /* Tx BD Retry Status */
`define ETH_TX_BD_RETLIM   32'h0008 /* Tx BD Retransmission Limit Status */
`define ETH_TX_BD_LATECOL  32'h0004 /* Tx BD Late Collision Status */
`define ETH_TX_BD_DEFER    32'h0002 /* Tx BD Defer Status */
`define ETH_TX_BD_CARRIER  32'h0001 /* Tx BD Carrier Sense Lost Status */
`define ETH_RX_BD_EMPTY    32'h8000 /* Rx BD Empty */
`define ETH_RX_BD_IRQ      32'h4000 /* Rx BD IRQ Enable */
`define ETH_RX_BD_WRAP     32'h2000 /* Rx BD Wrap (last BD) */
`define ETH_RX_BD_MISS     32'h0080 /* Rx BD Miss Status */
`define ETH_RX_BD_OVERRUN  32'h0040 /* Rx BD Overrun Status */
`define ETH_RX_BD_INVSIMB  32'h0020 /* Rx BD Invalid Symbol Status */
`define ETH_RX_BD_DRIBBLE  32'h0010 /* Rx BD Dribble Nibble Status */
`define ETH_RX_BD_TOOLONG  32'h0008 /* Rx BD Too Long Status */
`define ETH_RX_BD_SHORT    32'h0004 /* Rx BD Too Short Frame Status */
`define ETH_RX_BD_CRCERR   32'h0002 /* Rx BD CRC Error Status */
`define ETH_RX_BD_LATECOL  32'h0001 /* Rx BD Late Collision Status */
`define ETH_MODER      `ETH_BASE + 32'h00	/* Mode Register */
`define ETH_INT        `ETH_BASE + 32'h04	/* Interrupt Source Register */
`define ETH_INT_MASK   `ETH_BASE + 32'h08 /* Interrupt Mask Register */
`define ETH_IPGT       `ETH_BASE + 32'h0C /* Back to Bak Inter Packet Gap Register */
`define ETH_IPGR1      `ETH_BASE + 32'h10 /* Non Back to Back Inter Packet Gap Register 1 */
`define ETH_IPGR2      `ETH_BASE + 32'h14 /* Non Back to Back Inter Packet Gap Register 2 */
`define ETH_PACKETLEN  `ETH_BASE + 32'h18 /* Packet Length Register (min. and max.) */
`define ETH_COLLCONF   `ETH_BASE + 32'h1C /* Collision and Retry Configuration Register */
`define ETH_TX_BD_NUM  `ETH_BASE + 32'h20 /* Transmit Buffer Descriptor Number Register */
`define ETH_CTRLMODER  `ETH_BASE + 32'h24 /* Control Module Mode Register */
`define ETH_MIIMODER   `ETH_BASE + 32'h28 /* MII Mode Register */
`define ETH_MIICOMMAND `ETH_BASE + 32'h2C /* MII Command Register */
`define ETH_MIIADDRESS `ETH_BASE + 32'h30 /* MII Address Register */
`define ETH_MIITX_DATA `ETH_BASE + 32'h34 /* MII Transmit Data Register */
`define ETH_MIIRX_DATA `ETH_BASE + 32'h38 /* MII Receive Data Register */
`define ETH_MIISTATUS  `ETH_BASE + 32'h3C /* MII Status Register */
`define ETH_MAC_ADDR0  `ETH_BASE + 32'h40 /* MAC Individual Address Register 0 */
`define ETH_MAC_ADDR1  `ETH_BASE + 32'h44 /* MAC Individual Address Register 1 */
`define ETH_HASH_ADDR0 `ETH_BASE + 32'h48 /* Hash Register 0 */
`define ETH_HASH_ADDR1 `ETH_BASE + 32'h4C /* Hash Register 1 */
`define ETH_TX_CTRL    `ETH_BASE + 32'h50 /* Tx Control Register */
`define ETH_MODER_RXEN     32'h00000001 /* Receive Enable  */
`define ETH_MODER_TXEN     32'h00000002 /* Transmit Enable */
`define ETH_MODER_NOPRE    32'h00000004 /* No Preamble  */
`define ETH_MODER_BRO      32'h00000008 /* Reject Broadcast */
`define ETH_MODER_IAM      32'h00000010 /* Use Individual Hash */
`define ETH_MODER_PRO      32'h00000020 /* Promiscuous (receive all) */
`define ETH_MODER_IFG      32'h00000040 /* Min. IFG not required */
`define ETH_MODER_LOOPBCK  32'h00000080 /* Loop Back */
`define ETH_MODER_NOBCKOF  32'h00000100 /* No Backoff */
`define ETH_MODER_EXDFREN  32'h00000200 /* Excess Defer */
`define ETH_MODER_FULLD    32'h00000400 /* Full Duplex */
`define ETH_MODER_RST      32'h00000800 /* Reset MAC */
`define ETH_MODER_DLYCRCEN 32'h00001000 /* Delayed CRC Enable */
`define ETH_MODER_CRCEN    32'h00002000 /* CRC Enable */
`define ETH_MODER_HUGEN    32'h00004000 /* Huge Enable */
`define ETH_MODER_PAD      32'h00008000 /* Pad Enable */
`define ETH_MODER_RECSMALL 32'h00010000 /* Receive Small */
`define ETH_INT_TXB        32'h00000001 /* Transmit Buffer IRQ */
`define ETH_INT_TXE        32'h00000002 /* Transmit Error IRQ */
`define ETH_INT_RXB        32'h00000004 /* Receive Buffer IRQ */
`define ETH_INT_RXE        32'h00000008 /* Receive Error IRQ */
`define ETH_INT_BUSY       32'h00000010 /* Busy IRQ */
`define ETH_INT_TXC        32'h00000020 /* Transmit Control Frame IRQ */
`define ETH_INT_RXC        32'h00000040 /* Received Control Frame IRQ */
`define ETH_INT_MASK_TXB   32'h00000001 /* Transmit Buffer IRQ Mask */
`define ETH_INT_MASK_TXE   32'h00000002 /* Transmit Error IRQ Mask */
`define ETH_INT_MASK_RXF   32'h00000004 /* Receive Frame IRQ Mask */
`define ETH_INT_MASK_RXE   32'h00000008 /* Receive Error IRQ Mask */
`define ETH_INT_MASK_BUSY  32'h00000010 /* Busy IRQ Mask */
`define ETH_INT_MASK_TXC   32'h00000020 /* Transmit Control Frame IRQ Mask */
`define ETH_INT_MASK_RXC   32'h00000040 /* Received Control Frame IRQ Mask */
`define ETH_CTRLMODER_PASSALL 32'h00000001 /* Pass Control Frames */
`define ETH_CTRLMODER_RXFLOW  32'h00000002 /* Receive Control Flow Enable */
`define ETH_CTRLMODER_TXFLOW  32'h00000004 /* Transmit Control Flow Enable */
`define ETH_MIIMODER_CLKDIV   32'h000000FF /* Clock Divider */
`define ETH_MIIMODER_NOPRE    32'h00000100 /* No Preamble */
`define ETH_MIIMODER_RST      32'h00000200 /* MIIM Reset */
`define ETH_MIICOMMAND_SCANSTAT  32'h00000001 /* Scan Status */
`define ETH_MIICOMMAND_RSTAT     32'h00000002 /* Read Status */
`define ETH_MIICOMMAND_WCTRLDATA 32'h00000004 /* Write Control Data */
`define ETH_MIIADDRESS_FIAD 32'h0000001F /* PHY Address */
`define ETH_MIIADDRESS_RGAD 32'h00001F00 /* RGAD Address */
`define ETH_MIISTATUS_LINKFAIL    0 /* Link Fail bit */
`define ETH_MIISTATUS_BUSY        1 /* MII Busy bit */
`define ETH_MIISTATUS_NVALID      2 /* Data in MII Status Register is invalid bit */
`define ETH_TX_CTRL_TXPAUSERQ     32'h10000 /* Send PAUSE request */
`define TIME $display("  Time: %0t", $time)
`define ETH_MBIST_CTRL_WIDTH 3        // width of MBIST control bus
`define ETH_MODER_ADR         8'h0    // 0x0
`define ETH_INT_SOURCE_ADR    8'h1    // 0x4
`define ETH_INT_MASK_ADR      8'h2    // 0x8
`define ETH_IPGT_ADR          8'h3    // 0xC
`define ETH_IPGR1_ADR         8'h4    // 0x10
`define ETH_IPGR2_ADR         8'h5    // 0x14
`define ETH_PACKETLEN_ADR     8'h6    // 0x18
`define ETH_COLLCONF_ADR      8'h7    // 0x1C
`define ETH_TX_BD_NUM_ADR     8'h8    // 0x20
`define ETH_CTRLMODER_ADR     8'h9    // 0x24
`define ETH_MIIMODER_ADR      8'hA    // 0x28
`define ETH_MIICOMMAND_ADR    8'hB    // 0x2C
`define ETH_MIIADDRESS_ADR    8'hC    // 0x30
`define ETH_MIITX_DATA_ADR    8'hD    // 0x34
`define ETH_MIIRX_DATA_ADR    8'hE    // 0x38
`define ETH_MIISTATUS_ADR     8'hF    // 0x3C
`define ETH_MAC_ADDR0_ADR     8'h10   // 0x40
`define ETH_MAC_ADDR1_ADR     8'h11   // 0x44
`define ETH_HASH0_ADR         8'h12   // 0x48
`define ETH_HASH1_ADR         8'h13   // 0x4C
`define ETH_TX_CTRL_ADR       8'h14   // 0x50
`define ETH_RX_CTRL_ADR       8'h15   // 0x54
`define ETH_DBG_ADR           8'h16   // 0x58
`define ETH_MODER_DEF_0         8'h00
`define ETH_MODER_DEF_1         8'hA0
`define ETH_MODER_DEF_2         1'h0
`define ETH_INT_MASK_DEF_0      7'h0
`define ETH_IPGT_DEF_0          7'h12
`define ETH_IPGR1_DEF_0         7'h0C
`define ETH_IPGR2_DEF_0         7'h12
`define ETH_PACKETLEN_DEF_0     8'h00
`define ETH_PACKETLEN_DEF_1     8'h06
`define ETH_PACKETLEN_DEF_2     8'h40
`define ETH_PACKETLEN_DEF_3     8'h00
`define ETH_COLLCONF_DEF_0      6'h3f
`define ETH_COLLCONF_DEF_2      4'hF
`define ETH_TX_BD_NUM_DEF_0     8'h40
`define ETH_CTRLMODER_DEF_0     3'h0
`define ETH_MIIMODER_DEF_0      8'h64
`define ETH_MIIMODER_DEF_1      1'h0
`define ETH_MIIADDRESS_DEF_0    5'h00
`define ETH_MIIADDRESS_DEF_1    5'h00
`define ETH_MIITX_DATA_DEF_0    8'h00
`define ETH_MIITX_DATA_DEF_1    8'h00
`define ETH_MIIRX_DATA_DEF     16'h0000 // not written from WB
`define ETH_MAC_ADDR0_DEF_0     8'h00
`define ETH_MAC_ADDR0_DEF_1     8'h00
`define ETH_MAC_ADDR0_DEF_2     8'h00
`define ETH_MAC_ADDR0_DEF_3     8'h00
`define ETH_MAC_ADDR1_DEF_0     8'h00
`define ETH_MAC_ADDR1_DEF_1     8'h00
`define ETH_HASH0_DEF_0         8'h00
`define ETH_HASH0_DEF_1         8'h00
`define ETH_HASH0_DEF_2         8'h00
`define ETH_HASH0_DEF_3         8'h00
`define ETH_HASH1_DEF_0         8'h00
`define ETH_HASH1_DEF_1         8'h00
`define ETH_HASH1_DEF_2         8'h00
`define ETH_HASH1_DEF_3         8'h00
`define ETH_TX_CTRL_DEF_0       8'h00 //
`define ETH_TX_CTRL_DEF_1       8'h00 //
`define ETH_TX_CTRL_DEF_2       1'h0  //
`define ETH_RX_CTRL_DEF_0       8'h00
`define ETH_RX_CTRL_DEF_1       8'h00
`define ETH_MODER_WIDTH_0       8
`define ETH_MODER_WIDTH_1       8
`define ETH_MODER_WIDTH_2       1
`define ETH_INT_SOURCE_WIDTH_0  7
`define ETH_INT_MASK_WIDTH_0    7
`define ETH_IPGT_WIDTH_0        7
`define ETH_IPGR1_WIDTH_0       7
`define ETH_IPGR2_WIDTH_0       7
`define ETH_PACKETLEN_WIDTH_0   8
`define ETH_PACKETLEN_WIDTH_1   8
`define ETH_PACKETLEN_WIDTH_2   8
`define ETH_PACKETLEN_WIDTH_3   8
`define ETH_COLLCONF_WIDTH_0    6
`define ETH_COLLCONF_WIDTH_2    4
`define ETH_TX_BD_NUM_WIDTH_0   8
`define ETH_CTRLMODER_WIDTH_0   3
`define ETH_MIIMODER_WIDTH_0    8
`define ETH_MIIMODER_WIDTH_1    1
`define ETH_MIICOMMAND_WIDTH_0  3
`define ETH_MIIADDRESS_WIDTH_0  5
`define ETH_MIIADDRESS_WIDTH_1  5
`define ETH_MIITX_DATA_WIDTH_0  8
`define ETH_MIITX_DATA_WIDTH_1  8
`define ETH_MIIRX_DATA_WIDTH    16 // not written from WB
`define ETH_MIISTATUS_WIDTH     3 // not written from WB
`define ETH_MAC_ADDR0_WIDTH_0   8
`define ETH_MAC_ADDR0_WIDTH_1   8
`define ETH_MAC_ADDR0_WIDTH_2   8
`define ETH_MAC_ADDR0_WIDTH_3   8
`define ETH_MAC_ADDR1_WIDTH_0   8
`define ETH_MAC_ADDR1_WIDTH_1   8
`define ETH_HASH0_WIDTH_0       8
`define ETH_HASH0_WIDTH_1       8
`define ETH_HASH0_WIDTH_2       8
`define ETH_HASH0_WIDTH_3       8
`define ETH_HASH1_WIDTH_0       8
`define ETH_HASH1_WIDTH_1       8
`define ETH_HASH1_WIDTH_2       8
`define ETH_HASH1_WIDTH_3       8
`define ETH_TX_CTRL_WIDTH_0     8
`define ETH_TX_CTRL_WIDTH_1     8
`define ETH_TX_CTRL_WIDTH_2     1
`define ETH_RX_CTRL_WIDTH_0     8
`define ETH_RX_CTRL_WIDTH_1     8
`define ETH_REGISTERED_OUTPUTS
`define ETH_TX_FIFO_CNT_WIDTH  5
`define ETH_TX_FIFO_DEPTH      16
`define ETH_TX_FIFO_DATA_WIDTH 32
`define ETH_RX_FIFO_CNT_WIDTH  5
`define ETH_RX_FIFO_DEPTH      16
`define ETH_RX_FIFO_DATA_WIDTH 32
`define ETH_BURST_LENGTH       4    // Change also ETH_BURST_CNT_WIDTH
`define ETH_BURST_CNT_WIDTH    3    // The counter must be width enough to count to ETH_BURST_LENGTH

