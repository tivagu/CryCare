#include "crycare_protocols.h"

uint8_t checksum_xor(const crycare_packet_t *pkt){
    if (pkt == NULL) return 0;
    const uint8_t *bytes = (const uint8_t *) pkt; // typecast from sizeof(pkt) 16bytes to 1 byte for calculate 1 byte each time
    uint8_t sum = 0;
    for (int i = 0; i < sizeof(crycare_packet_t) -1; i++){
        sum ^= bytes[i];
    }
    return sum;
}


