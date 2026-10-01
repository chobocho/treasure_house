// 슬라이드 p6-v5-style-eap — XxxAsync + XxxCompleted(EAP), C# 5.0
using System;
using System.ComponentModel;
using System.IO;
using System.Text;
using System.Threading;

class ChunkReader
{
    readonly Stream s;
    public ChunkReader(Stream s) { this.s = s; }
    public event EventHandler<ReadEventArgs> ReadCompleted;

    public void ReadAsync(byte[] buf)
    {
        ThreadPool.QueueUserWorkItem(_ =>
        {
            int n = 0; Exception error = null;
            try { n = s.Read(buf, 0, buf.Length); }
            catch (Exception e) { error = e; }
            ReadCompleted(this, new ReadEventArgs(n, error));
        });
    }
}

class ReadEventArgs : AsyncCompletedEventArgs
{
    public readonly int Count;
    public ReadEventArgs(int count, Exception error)
        : base(error, false, null) { Count = count; }
}
