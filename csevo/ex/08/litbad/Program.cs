// 슬라이드 p8-v7-literals-where — 밑줄이 갈 수 없는 자리, C# 7.0
class App
{
    static void Main()
    {
        int a = 1_;          // last character
        double b = 1_.5;     // next to the decimal point
        double c = 1.5_e3;   // next to the exponent character
        double d = 1e_3;     // right after the exponent character
        float f = 10_f;      // next to the type suffix
    }
}
