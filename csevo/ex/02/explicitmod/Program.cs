// 슬라이드 p2-v1-explicitfail — 명시적 구현에 붙일 수 없는 것, C# 1.0
interface ILog { void Write(string s); }

class FileLog : ILog
{
    public void ILog.Write(string s) { }          // no modifiers
    void ILog.Flush() { }                         // not in ILog
}

class App
{
    static void Main() { }
}
