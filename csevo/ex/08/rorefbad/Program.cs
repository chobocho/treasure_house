// 슬라이드 p8-v7_2-refreadonly-bad — ref readonly 로 막힌 것, C# 7.2
struct Big { public long A; }

class App
{
    static Big[] items = new Big[2];
    static readonly Big RO;

    static ref readonly Big At(int i) => ref items[i];
    static ref readonly Big Echo(in Big b) => ref b;
    static void Inc(ref long n) { n++; }

    static ref readonly Big Leak()
    {
        return ref Echo(default(Big));   // a temp would escape
    }

    static void Main()
    {
        ref Big w = ref At(0);           // drop the readonly
        At(0).A = 5;                     // write through it
        Inc(ref At(0).A);                // pass a field as ref
        ref Big f = ref RO;              // a readonly field
        ref readonly Big ok = ref RO;    // this one is fine
    }
}
