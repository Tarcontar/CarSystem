
#include "SPI.h"
//#include <softwareserial.h>

#define DataOut 12
#define BUFFER 10

#define BYTES_DELAY 874 // 874 750
#define PACKET_DELAY 41

#define Data_out_interrupt 0

#define CDC_PREFIX1 0x53
#define CDC_PREFIX2 0x2C

#define CDC_END_CMD 0x14
#define CDC_END_CMD2 0x38
#define CDC_PLAY 0xE4
#define CDC_STOP 0x10
#define CDC_NEXT 0xF8
#define CDC_PREV 0x78
#define CDC_SEEK_FWD 0xD8
#define CDC_SEEK_RWD 0x58
#define cd1 0x0C
#define cd2 0x8C
#define cd3 0x4C
#define cd4 0xCC
#define cd5 0x2C
#define cd6 0xAC
#define CDC_SCAN 0xA0
#define CDC_SFL 0x60
#define CDC_PLAY_NORMAL 0x08

#define MODE_PLAY 0xFF
#define MODE_SHFFL 0x55
#define MODE_SCAN 0x00

volatile uint16_t captimehi = 0;
volatile uint16_t captimelo = 0;
volatile uint8_t capturingstart = 0;
volatile uint8_t capturingbytes = 0;
volatile uint32_t cmd [BUFFER];
volatile uint8_t cmd_write_buffer_pointer = 0;
volatile uint8_t cmd_read_buffer_pointer = 0;
volatile uint8_t cmdbit = 0;
volatile uint8_t newcmd [BUFFER];
volatile uint8_t prev_cmd = 0;

volatile uint8_t cd = 0xBE;
volatile uint8_t tr = 0xFE;
volatile uint8_t mode = MODE_PLAY;
volatile uint8_t idle = 1;
volatile uint8_t load_cd = 0;

uint8_t getCommand (uint32_t cmd2);
void send_package (uint8_t c0, uint8_t c1, uint8_t c2, uint8_t c3, uint8_t c4, uint8_t c5, uint8_t c6, uint8_t c7);
void read_Data_out ();
void prev_song();
void toggle_play_mode();
void next_song();
void play_cd (uint8_t cd);

void setup() 
{
  pinMode (DataOut, INPUT_PULLUP);
  attachInterrupt (Data_out_interrupt, read_Data_out, CHANGE);
  cli (); //stop interrupts
  TCCR1A = 0; // set entire TCCR1A register to 0
  TCCR1B = 0; // same for TCCR1B
  TCNT1 = 0; // initialize counter value to 0
  // Set CS11 bit for 8 => tick every 1us @ 8MHz, 0.5us @ 16MHz
  // Set CS11 bit and CS10 for 64 prescaler => tick every 8us @ 8MHz, 4us @ 16MHz
  TCCR1B |= (1 << CS11); // | (1 << CS10);
  sei(); // allow interrupts
  Serial.begin(9600);
  Serial.println("start");
  SPI.begin();
  SPI.setBitOrder(MSBFIRST);
  SPI.setDataMode(SPI_MODE1);
  //SPI.setClockDivider(SPI_CLOCK_DIV128); // 62.5kHz@8MHz 125kHz @ 16MHz
  SPI.setClockDivider(SPI_CLOCK_DIV64); //125kHz@8MHz

  send_package (0x74, 0xBE, 0xFE, 0xFF, 0xFF, mode, 0x8F, 0x7C); // idle
  delay(10);
  send_package (0x34, 0xFF, 0xFE, 0xFE, 0xFE, 0xFF, 0xFA, 0x3C); //load disc
  delay(100);
  send_package (0x74, 0xBE, 0xFE, 0xFF, 0xFF, mode, 0x8F, 0x7C); // idle
  delay(10);

  while(1)
  {
    send_package(0x34, cd, tr, 0xFF, 0xFF, 0xFF, 0xCF, 0x3C);
    delay(PACKET_DELAY);

    if (digitalRead(DataOut))
    {
      if (capturingstart || capturingbytes)
      {
        captimelo = TCNT1;
      }
      else
      {
        capturingstart = 1; 
     }
      TCNT1 = 0;

      // eval times
      // tick @ 0.5us
      // 9000us HIGH and 4500us LOW
      Serial.println(captimehi);
      Serial.println(captimelo);
      if (captimehi > 8300 && captimelo > 3500) // && captimehi < 19000/8 && captimelo < 10000)
      {
        capturingstart = 0;
        capturingbytes = 1;
        Serial.println("startseq Found ");
      }// Logic one = 1700us
      else if(capturingbytes && captimelo > 1500) // && captimelo < 3500)
      {
        Serial.println("bit 1 ");
        cmd[cmd_write_buffer_pointer] = (cmd [cmd_write_buffer_pointer] << 1) | 0x00000001;
        cmdbit ++;
      }
      else if (capturingbytes && captimelo > 500)// && captimelo < 1200)
      {
        Serial.println("bit 0 ");
        cmd[cmd_write_buffer_pointer] = (cmd[cmd_write_buffer_pointer] << 1);
        cmdbit ++;
      }

      if (cmdbit == 32)
      {
        Serial.println("32bit");
        Serial.println(cmd[cmd_write_buffer_pointer], HEX);
        newcmd[cmd_write_buffer_pointer] = 1;
        capturingbytes = 0;
        cmdbit = 0;
        cmd_write_buffer_pointer ++;
        if (cmd_write_buffer_pointer == BUFFER)
          cmd_write_buffer_pointer = 0;
      }
    }
    else
    {
      captimehi = TCNT1;
      TCNT1 = 0;
    }
  }

  for (int cmd_read_buffer_pointer = 0; cmd_read_buffer_pointer < BUFFER; cmd_read_buffer_pointer++)
   {
      Serial.println("test");
      if (newcmd [cmd_read_buffer_pointer])
      {
          //Tmp_cmd = getCommand(cmd);
          Serial.println(cmd[cmd_read_buffer_pointer], HEX);
          switch( getCommand (cmd [cmd_read_buffer_pointer]))
          {
            case CDC_STOP:
              prev_cmd = CDC_STOP;
              break;
            case CDC_PLAY_NORMAL:
              prev_cmd = CDC_PLAY_NORMAL;
              break;
            case CDC_PLAY:
              prev_cmd = CDC_PLAY;
              break;
            case CDC_PREV:
              prev_cmd = CDC_PREV;
              break;
            case CDC_NEXT:
              prev_cmd = CDC_NEXT;
              break;
            case cd1:
              prev_cmd = cd1;
              break;
            case cd2:
              prev_cmd = cd2;
              break;
            case cd3:
              prev_cmd = cd3;
              break;
            case cd4:
              prev_cmd = cd4;
              break;
            case cd5:
              prev_cmd = cd5;
              break;
            case cd6:
              prev_cmd = cd6;
              break;
            case CDC_END_CMD:
              if (prev_cmd == CDC_PLAY_NORMAL || prev_cmd == CDC_PLAY)
              {
                 idle = 0;
                 mode = MODE_PLAY;
                 toggle_play_mode();
              }
              else if (prev_cmd == CDC_PREV)
              {
                idle = 0;
                tr++;
                prev_song();
              }
              else if (prev_cmd == CDC_NEXT)
              {
                idle = 0;
                tr--;
                next_song();
              }
              else if (prev_cmd == CDC_STOP)
              {
                idle = 1;
                toggle_play_mode();
              }
              prev_cmd = 0;
              break;
            case CDC_END_CMD2:
              if (prev_cmd == cd1)
              {
                idle = 0;
                cd = 0xBE;
                play_cd(cd);
              }
              else if (prev_cmd == cd2)
              {
                idle = 0;
                cd = 0xBD;
                play_cd(cd);
              }
              else if (prev_cmd == cd3)
              {
                idle = 0;
                cd = 0xBC;
                play_cd(cd);
              }
              else if (prev_cmd == cd4)
              {
                idle = 0;
                cd = 0xBB;
                play_cd(cd);
              }
              else if (prev_cmd == cd5)
              {
                idle = 0;
                cd = 0xBA;
                play_cd(cd);
              }
              else if (prev_cmd == cd6)
              {
                idle = 0;
                cd = 0xB9;
                play_cd(cd);
              }
              prev_cmd = 0;
              break;
          }
          newcmd [cmd_read_buffer_pointer] = 0;
          Serial.print("CD:");
          Serial.print(cd, HEX);
          Serial.print("TR:");
          Serial.print("mode:");
          Serial.print(mode, HEX);
          Serial.print("idle:");
          Serial.print(idle);
      }
   }  
}



void loop()
{
  /*
   
 
   if (idle)
   {
    send_package(0x34, cd, tr, 0xFF, 0xFF, mode, 0xCF, 0x3C);
   }
   else 
   {
    send_package(0x34, cd, tr, 0xFF, 0xFF, mode, 0xCF, 0x3C);
   }
  
  i++;
  if (i > 1000)
  {
    i = 0;
    cd--;
    tr--;
  }
  */

}

uint8_t getCommand(uint32_t cmd2)
{
  if (((cmd2 >> 24) & 0xFF) == CDC_PREFIX1 && ((cmd2 >> 16) & 0xFF) == CDC_PREFIX2)
    if (((cmd2 >> 8) & 0xFF) == (0xFF ^ ((cmd2) & 0xFF)))
      return (cmd2 >> 8) & 0xFF;
  return 0;
}

void send_package(uint8_t c0, uint8_t c1, uint8_t c2, uint8_t c3, uint8_t c4, uint8_t c5, uint8_t c6, uint8_t c7)
{
  SPI.transfer(c0);
  delayMicroseconds(BYTES_DELAY);
  SPI.transfer(c1);
  delayMicroseconds(BYTES_DELAY);
  SPI.transfer(c2);
  delayMicroseconds(BYTES_DELAY);
  SPI.transfer(c3);
  delayMicroseconds(BYTES_DELAY);
  SPI.transfer(c4);
  delayMicroseconds(BYTES_DELAY);
  SPI.transfer(c5);
  delayMicroseconds(BYTES_DELAY);
  SPI.transfer(c6);
  delayMicroseconds(BYTES_DELAY);
  SPI.transfer(c7);
}

void read_Data_out() // remote signals
{
  // if (newcmd == 0) {
  if (digitalRead(DataOut))
  {
    if (capturingstart || capturingbytes)
    {
      captimelo = TCNT1;
    }
    else
    {
      capturingstart = 1;
      TCNT1 = 0;
    }

    // eval times
    // tick @ 0.5us
    // 9000us HIGH and 4500us LOW
    if (captimehi > 17000 && captimelo > 8000) // && captimehi < 19000/8 && captimelo < 10000)
    {
      capturingstart = 0;
      capturingbytes = 1;
      //Cmdbit = 0;
      //Cmd = 0;
      //Serial.println("startseq Found ");
    }// Logic one = 1700us
    else if(capturingbytes && captimelo > 3300) // && captimelo < 3500)
    {
      //Serial.println("bit 1 ");
      cmd[cmd_write_buffer_pointer] = (cmd [cmd_write_buffer_pointer] << 1) | 0x00000001;
      cmdbit ++;
    }
    else if (capturingbytes && captimelo > 1000)// && captimelo < 1200)
    {
      //Serial.println("bit 0 ");
      cmd[cmd_write_buffer_pointer] = (cmd[cmd_write_buffer_pointer] << 1);
      cmdbit ++;
    }

    if (cmdbit == 32)
    {
      //Serial.println("32bit");
      //Serial.println(cmd[cmd_write_buffer_pointer], HEX);
      newcmd[cmd_write_buffer_pointer] = 1;
      capturingbytes = 0;
      cmdbit = 0;
      cmd_write_buffer_pointer ++;
      if (cmd_write_buffer_pointer == BUFFER)
        cmd_write_buffer_pointer = 0;
    }
  }
  else
  {
    captimehi = TCNT1;
    TCNT1 = 0;
  }
  //}
}



