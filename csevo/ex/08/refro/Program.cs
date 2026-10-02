// 슬라이드 p8-v7-ref-ro — 읽기 전용 저장소는 ref 로 못 내준다, C# 7.0
class App
{
    static readonly int Limit = 10;
    static string text = "abc";
    static int Prop { get; set; }

    static ref int Ro() { return ref Limit; }       // readonly field
    static ref char Ch() { return ref text[0]; }    // string indexer
    static ref int P() { return ref Prop; }         // a property

    static void Main()
    {
    }
}
