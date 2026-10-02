// 슬라이드 p8-v7-ref-local — 프레임과 함께 죽는 것, C# 7.0
class App
{
    static int field;

    static ref int Local()
    {
        int x = 1;
        return ref x;            // x dies with this frame
    }

    static ref int ByValue(int p)
    {
        return ref p;            // p is a copy: it dies too
    }

    static ref int Caller(ref int p) { return ref p; }  // ok
    static ref int Field() { return ref field; }        // ok
    static ref int Heap(int[] a) { return ref a[0]; }   // ok

    static void Main()
    {
    }
}
